import math
import ast
import inspect
import textwrap

#############################################
#############################################
# YOUR CODE BELOW
#############################################

# Implement `constexpr` and `eval_const_exprs`

def constexpr(func):
    func.is_marked_constexpr = True
    return func


class ConstExpressionEvaluator(ast.NodeTransformer):
    def __init__(self, global_namespace):
        self.global_namespace = global_namespace
    
    def visit_Call(self, node):
        self.generic_visit(node)
        
        if isinstance(node.func, ast.Name):
            function_name = node.func.id
            
            if function_name in self.global_namespace:
                function = self.global_namespace[function_name]
                
                if hasattr(function, 'is_marked_constexpr') and function.is_marked_constexpr:
                    if self.are_all_args_const(node):
                        args = [self.eval_const(arg) for arg in node.args]
                        keyword_args = {keyword.arg: self.eval_const(keyword.value) for keyword in node.keywords}
                        
                        result = function(*args, **keyword_args)
                        
                        return ast.Constant(value=result)
        
        return node
    
    def are_all_args_const(self, node):
        for argument in node.args:
            if not self.is_const(argument):
                return False
        
        for keyword_argument in node.keywords:
            if not self.is_const(keyword_argument.value):
                return False
        
        return True
     
    def is_const(self, node):
        if isinstance(node, ast.Constant):
            return True
        elif isinstance(node, (ast.BinOp, ast.UnaryOp)):
            return self.is_const_expression(node)
        return False
    
    def is_const_expression(self, node):
        if isinstance(node, ast.Constant):
            return True
        elif isinstance(node, ast.BinOp):
            return self.is_const_expression(node.left) and self.is_const_expression(node.right)
        elif isinstance(node, ast.UnaryOp):
            return self.is_const_expression(node.operand)
        return False
    
    def eval_const(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, (ast.BinOp, ast.UnaryOp)):
            expression = ast.Expression(body=node)
            compiled_code = compile(expression, '<string>', 'eval')
            return eval(compiled_code)
        return None


def eval_const_exprs(function):
    source = inspect.getsource(function)
    source = textwrap.dedent(source)
    
    syntax_tree = ast.parse(source)
    
    namespace = function.__globals__.copy()
    
    if function.__closure__:
        closure_variables = inspect.getclosurevars(function)
        namespace.update(closure_variables.nonlocals)
    
    evaluator = ConstExpressionEvaluator(namespace)
    new_syntax_tree = evaluator.visit(syntax_tree)
    
    ast.fix_missing_locations(new_syntax_tree)
    
    function_definition = new_syntax_tree.body[0]
    function_definition.decorator_list = []
    
    compiled_code = compile(ast.Module(body=[function_definition], type_ignores=[]), '<string>', 'exec')
    
    new_namespace = {}
    exec(compiled_code, namespace, new_namespace)
    
    modified_function = new_namespace[function.__name__]
    
    return modified_function

#############################################


# Execution Marker is only used for instrumentation
# and tests, do not consider it as a state change. In
# other words, it does not make a pure function "not pure".
class ExecutionMarker:
    def __init__(self):
        self.counter = 0
    def mark(self):
        self.counter += 1
    def reset(self):
        self.counter = 0


def test_simple():
    _m = ExecutionMarker()

    @constexpr
    def f(a, b):
        _m.mark()
        return a + b

    @eval_const_exprs
    def my_function(a):
        return f(3, 6) + f(a, 3)

    _m.reset()
    result = my_function(8)
    assert result == 3+6 + 8+3, f"Res {result}"
    assert _m.counter == 1, _m.counter


def test_larger():
    _m = ExecutionMarker()

    @constexpr
    def f(a, b):
        _m.mark()
        return int(math.exp(b + a))

    @constexpr
    def g(a, b):
        _m.mark()
        return a - b

    @eval_const_exprs
    def my_function(a):
        result = f(-3, 3)
        result = result + f(a, 8)
        return g(result, 2) + g(333, 330)

    _m.reset()
    res = my_function(-8)
    assert res == 3, res
    assert _m.counter == 2, _m.counter


def test_multi():
    _m = ExecutionMarker()

    @constexpr
    def f(a, b):
        _m.mark()
        return int(math.exp(a + b))

    @constexpr
    def g(a, b):
        _m.mark()
        return a - b

    @eval_const_exprs
    def my_function(a):
        result = f(g(0, 3), 3) + g(3, a)
        return result

    _m.reset()
    out = my_function(3)
    assert out == 1, out
    assert _m.counter == 1, _m.counter


# Extra points.
def test_advanced():
    _m = ExecutionMarker()

    @constexpr
    def f(a, b):
        _m.mark()
        return int(math.exp(a + b))

    @eval_const_exprs
    def my_function(a):
        result = f(3 - 3, 0) + f(3, a)
        return result

    _m.reset()
    res = my_function(-3)
    assert res == 2, res
    assert _m.counter == 1, _m.counter