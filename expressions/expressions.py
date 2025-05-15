"""doc."""
import numbers
from functools import singledispatch


class Expression:
    """doc."""

    def __init__(self, *operands):
        """doc."""
        self.operands = operands

    @staticmethod
    def _promote(other):
        if isinstance(other, Expression):
            return other
        elif isinstance(other, numbers.Number):
            return Number(other)          # 数字 → Number
        elif isinstance(other, str):
            return Symbol(other)          # 额外支持 'x' → Symbol
        else:
            raise TypeError("Unsupported operand")

    def __add__(self, other):
        """doc."""
        return Add(self, Expression._promote(other))

    def __radd__(self, other):
        """doc."""
        return Add(Expression._promote(other), self)

    def __sub__(self, other):
        """doc."""
        return Sub(self, Expression._promote(other))

    def __rsub__(self, other):
        """doc."""
        return Sub(Expression._promote(other), self)

    def __mul__(self, other):
        """doc."""
        return Mul(self, Expression._promote(other))

    def __rmul__(self, other):
        """doc."""
        return Mul(Expression._promote(other), self)

    def __truediv__(self, other):
        """doc."""
        return Div(self, Expression._promote(other))

    def __rtruediv__(self, other):
        """doc."""
        return Div(Expression._promote(other), self)

    def __pow__(self, other):
        """doc."""
        return Pow(self, Expression._promote(other))

    def __rpow__(self, other):
        """doc."""
        return Pow(Expression._promote(other), self)


class Terminal(Expression):
    """doc."""

    def __init__(self, value):
        """doc."""
        self.value = value
        super().__init__()

    def __repr__(self):
        """doc."""
        return repr(self.value)

    def __str__(self):
        """doc."""
        return str(self.value)


class Operator(Expression):
    """doc."""

    def __repr__(self):
        """doc."""
        return type(self).__name__ + repr(self.operands)

    def __str__(self):
        """doc."""
        e1, e2 = self.operands
        e1str = f"{e1}"
        if isinstance(e1, Operator):
            if e1.pref > self.pref:
                e1str = f"({e1})"
        e2str = f"{e2}"
        if isinstance(e2, Operator):
            if e2.pref > self.pref:
                e2str = f"({e2})"
        return e1str + f" {self.symbol} " + e2str


class Number(Terminal):
    """doc."""

    def __init__(self, value):
        """doc."""
        if not isinstance(value, numbers.Number):
            raise TypeError("Number expects a numeric value")
        super().__init__(value)


class Symbol(Terminal):
    """doc."""

    def __init__(self, name):
        """doc."""
        if not isinstance(name, str):
            raise TypeError("Symbol expects a string")
        super().__init__(name)


class Add(Operator):
    """doc."""

    symbol = "+"
    pref = 3


class Mul(Operator):
    """doc."""

    symbol = "*"
    pref = 2


class Sub(Operator):
    """doc."""

    symbol = "-"
    pref = 3


class Div(Operator):
    """doc."""

    symbol = "/"
    pref = 2


class Pow(Operator):
    """doc."""

    symbol = "^"
    pref = 1


def postvisitor(expr, fn, **kwargs):
    """根本没明白为啥这样写."""
    stack = [(expr, False)]        # (node, children_done_flag)
    seen = set()                  # id(node) 已算完
    results = {}                     # node -> fn 返回值

    while stack:
        node, done = stack.pop()

        if done:                     # 孩子都算完，处理自己
            child_vals = [results[c] for c in node.operands]
            results[node] = fn(node, *child_vals, **kwargs)
            seen.add(id(node))
        else:
            if id(node) in seen:     # 这个节点以前算过，跳过
                continue
            # 第一次见：先放回栈标记 done=True，再压孩子
            stack.append((node, True))
            for child in node.operands:          # 后序=先压右后压左都可以
                if id(child) not in seen:
                    stack.append((child, False))

    return results[expr]


@singledispatch
def differentiate(expr, *child_ders, var):
    """doc."""
    raise NotImplementedError(...)


@differentiate.register(Number)
def _(expr, *_, var):
    return Number(0)


@differentiate.register(Symbol)
def _(expr, *_, var):
    return Number(1) if expr.value == var else Number(0)


@differentiate.register(Add)
def _(expr, left_d, right_d, *, var):
    return Add(left_d, right_d)


@differentiate.register(Mul)
def _(expr, left_d, right_d, *, var):
    u, v = expr.operands           # 原来的两个因子
    # (u·v)' = u'·v + u·v'
    return Add(Mul(left_d, v), Mul(u, right_d))


@differentiate.register(Div)
def _(expr, left_d, right_d, *, var):
    u, v = expr.operands           # 原来的两个因子
    # (u/v)' = (u'·v - u·v')/v^2
    return Div(Sub(Mul(left_d, v), Mul(u, right_d)), Pow(v, Number(2)))


@differentiate.register(Pow)
def _(expr, left_d, right_d, *, var):
    u, v = expr.operands           # 原来的两个因子
    # (u^c)' = c·u^(c-1)
    return Mul(v, Pow(u, v-1))
