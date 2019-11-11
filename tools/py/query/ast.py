#versa.query.ast

from versa.util import column


class query(object):
    'Versa query language abstract syntax tree expression instance'
    def traverse(self):
        yield self.left
        yield self.right

    def evaluate(self, ctx):
        #Walk the tree and prepare the nodes
        if hasattr(self, 'traverse'):
            for node in self.traverse():
                print(1, node)
                if hasattr(node, 'prepare'):
                    node.prepare(ctx)


class conjunction(query):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def traverse(self):
        if hasattr(self.left, 'traverse'):
            yield from self.left.traverse()
        if hasattr(self.right, 'traverse'):
            yield from self.right.traverse()
        yield self

    def _evaluate(self, ctx):
        return bool(self.left._evaluate(ctx) or self.right._evaluate(ctx))

    def evaluate(self, ctx):
        query.evaluate(self, ctx)
        self._evaluate(ctx)


class disjunction(query):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def traverse(self):
        if hasattr(self.left, 'traverse'):
            yield from self.left.traverse()
        if hasattr(self.right, 'traverse'):
            yield from self.right.traverse()
        yield self

    def _evaluate(self, ctx):
        return bool(self.left._evaluate(ctx) or self.right._evaluate(ctx))

    def evaluate(self, ctx):
        query.evaluate(self, ctx)
        self._evaluate(ctx)


class stringseq(query):
    def __init__(self, items):
        self.items = items

    def traverse(self):
        yield from self.items
        yield self

    def _evaluate(self, ctx):
        return ''.join((i if isinstance(i, str) else i._evaluate(ctx) for i in self.items))

    def evaluate(self, ctx):
        query.evaluate(self, ctx)
        self._evaluate(ctx)


class variable(query):
    def __init__(self, name):
        self.name = name
        self.cached_possible_values = None

    def update_match_hints__premature_optimization_edition(self, ctx, role):
        possible_values = set(column(ctx.model, role))
        #Match_hints are used to narrow down possible variable values based on the contents of the input model
        match_roles = ctx.extras.setdefault('match_roles', {})
        match_possible_values = ctx.extras.setdefault('match_possible_values', {})
        if self.name not in match_roles:
            match_roles.setdefault(self.name, []).append(role)
            match_possible_values[self.name] = possible_values
        elif role not in match_roles[self.name]:
            match_roles.setdefault(self.name, []).append(role)
            match_possible_values[self.name].intersection_update(possible_values)
        print(match_roles)
        print(match_possible_values)
        return

    def _evaluate(self, ctx):
        return ctx.extras['match_possible_values'][self.name]

    def evaluate(self, ctx):
        query.evaluate(self, ctx)
        self._evaluate(ctx)


class constant(query):
    def __init__(self, name):
        self.name = name

    def _evaluate(self, ctx):
        return ctx.variables[self.name]

    def evaluate(self, ctx):
        query.evaluate(self, ctx)
        self._evaluate(ctx)

class negation(query):
    def __init__(self, right):
        self.right = right

    def traverse(self):
        yield self.right
        yield self

    def _evaluate(self, ctx):
        return not bool(self.right._evaluate(ctx))

    def evaluate(self, ctx):
        query.evaluate(self, ctx)
        self._evaluate(ctx)


class funccall(query):
    def __init__(self, name, arglist):
        self.name = name
        self.arglist = arglist

    def traverse(self):
        for arg in self.arglist:
            yield arg
        yield self

    #def prepare(self, ctx):
        #if self.name == '?':
            #Match request
            #for ix, arg in enumerate(self.arglist):
                #if isinstance(arg, variable):
                    #arg.update_match_hints(ctx, ix)

    def _evaluate(self, ctx):
        if self.name == '?':
            passed_args = [ None if isinstance(a, variable) else a.evaluate(ctx) for a in self.arglist ]
            #Match request
            result = match_result(ctx)
            for ix, link in ctx.model.match(*passed_args):
                if isinstance(self.arglist[0], variable):
                    result.variables = self.arglist[0].name
        else:
            raise NotImplementedError

    def evaluate(self, ctx):
        query.evaluate(self, ctx)
        self._evaluate(ctx)


class match_result(object):
    def __init__(self, context):
        self.model = context.transform_factory()
        self.variables = {}

    def conjoin(other):
        pass
