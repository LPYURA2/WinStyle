"""Bounded static dependency plan. Never uses OS loader, filesystem or executes code."""
from dataclasses import dataclass
import re
from pecheck import Image, Rejected, require
from peexports import inspect_dll

MAX_MODULES = 64
MAX_CATALOG_BYTES = 128 * 1024 * 1024
MAX_WORK = 65536
MAX_FORWARDERS = 32

def module_key(value, *, forwarder=False):
    require(type(value) is str and 1 <= len(value) <= 255
            and re.fullmatch(r'[A-Za-z0-9_+.-]+', value) is not None
            and not value.startswith('.') and not value.endswith('.')
            and '..' not in value, 'unsupported module basename')
    value = value.lower()
    if forwarder and not value.endswith('.dll'):
        value += '.dll'
    require(value.endswith('.dll'), 'expected DLL basename')
    return value

@dataclass(frozen=True)
class Binding:
    owner: str
    imported_module: str
    symbol: str | int
    target_module: str
    target_rva: int

@dataclass(frozen=True)
class Plan:
    modules: tuple[str, ...]
    bindings: tuple[Binding, ...]
    execution_allowed: bool = False

class Resolver:
    def __init__(self, catalog):
        require(type(catalog) is dict and len(catalog) <= MAX_MODULES, 'catalog limit')
        self.catalog = {}
        size = 0
        for name, raw in catalog.items():
            key = module_key(name)
            require(key not in self.catalog, 'duplicate module name')
            require(type(raw) is bytes, 'immutable DLL required')
            size += len(raw)
            require(size <= MAX_CATALOG_BYTES, 'catalog byte limit')
            self.catalog[key] = raw
        self.modules = {}
        self.work = 0

    def tick(self, n=1):
        self.work += n
        require(self.work <= MAX_WORK, 'resolution work limit')

    def load(self, key):
        if key not in self.modules:
            require(key in self.catalog, 'missing DLL: '+key)
            raw = self.catalog[key]
            report = inspect_dll(raw)
            img = Image(raw, allow_dll=True)
            names, ords = {}, {}
            for item in report['exports']:
                self.tick(1+len(item['names']))
                ords[item['ordinal']] = item
                for name in item['names']:
                    names[name] = item
            self.modules[key] = (img, names, ords)
        return self.modules[key]

    def resolve(self, module, symbol):
        key = module_key(module)
        visited = set()
        for _ in range(MAX_FORWARDERS+1):
            self.tick()
            require(type(symbol) in (str, int), 'invalid symbol type')
            if type(symbol) is int:
                require(0 <= symbol <= 0xffffffff, 'invalid ordinal')
            else:
                require(0 < len(symbol) <= 4096, 'invalid symbol name')
            _, names, ords = self.load(key)
            entry = (ords if type(symbol) is int else names).get(symbol)
            require(entry is not None, f'missing export: {key}!{symbol}')
            identity = (key, entry['ordinal'])
            require(identity not in visited, 'forwarder cycle')
            visited.add(identity)
            if entry['forwarder'] is None:
                return key, entry['rva']
            mod, _, symbol = entry['forwarder'].rpartition('.')
            key = module_key(mod, forwarder=True)
            if symbol.startswith('#'):
                symbol = int(symbol[1:])
        raise Rejected('forwarder depth limit')

def plan(raw, catalog):
    require(type(raw) is bytes, 'immutable EXE required')
    exe = Image(raw)
    resolver = Resolver(catalog)
    bindings = []
    handled = set()

    def process(owner, img):
        for dll, symbols in img.import_refs:
            key = module_key(dll)
            resolver.load(key)
            for symbol in symbols:
                resolver.tick()
                target, rva = resolver.resolve(key, symbol)
                bindings.append(Binding(owner, key, symbol, target, rva))

    process('<exe>', exe)
    # Modules loaded by forwarders also need their normal imports inspected.
    # Ordinary dependency graph cycles are visited once, not mistaken for forwarder cycles.
    while True:
        pending = [key for key in resolver.modules if key not in handled]
        if not pending:
            break
        for key in pending:
            handled.add(key)
            process(key, resolver.modules[key][0])
    return Plan(tuple(resolver.modules), tuple(bindings))
