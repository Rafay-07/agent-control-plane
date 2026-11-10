"""Tool registry with argument validation and role-based access control."""


class ToolError(Exception):
    pass


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, schema, roles=("user", "admin")):
        """Decorator. schema maps arg name -> type, e.g. {"order_id": str}."""
        def deco(fn):
            self._tools[name] = (fn, schema, set(roles))
            return fn
        return deco

    def names_for(self, role):
        return [n for n, (_, _, roles) in self._tools.items() if role in roles]

    def call(self, name, args, role):
        if name not in self._tools:
            raise ToolError(f"unknown tool: {name}")
        fn, schema, roles = self._tools[name]
        if role not in roles:
            raise ToolError(f"role '{role}' may not call {name}")
        for key, typ in schema.items():
            if key not in args:
                raise ToolError(f"missing argument: {key}")
            if not isinstance(args[key], typ):
                raise ToolError(f"argument {key} must be {typ.__name__}")
        extra = set(args) - set(schema)
        if extra:
            raise ToolError(f"unexpected arguments: {sorted(extra)}")
        return fn(**args)


def default_registry():
    reg = ToolRegistry()
    orders = {"A100": "shipped, arrives Friday", "A200": "processing", "A300": "delivered"}

    @reg.register("lookup_order", {"order_id": str})
    def lookup_order(order_id):
        return orders.get(order_id, "not found")

    @reg.register("create_ticket", {"summary": str}, roles=("admin",))
    def create_ticket(summary):
        return f"ticket created: {summary}"

    @reg.register("calculate", {"numbers": list})
    def calculate(numbers):
        return str(sum(numbers))

    @reg.register("get_weather", {"city": str})
    def get_weather(city):
        return f"{city}: 5C, cloudy"

    return reg
