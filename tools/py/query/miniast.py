#versa.query.ast

from versa.util import column


class query(object):
    'Versa query language abstract syntax tree expression instance'
    pass

class conjunction(query):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def evaluate(self, ctx):
        #FIXME: what the heck do we do for the conjunctive case of matches?
        left, right = self.left.evaluate(ctx), self.right.evaluate(ctx)
        if isinstance(left, funccall):
            #Match result
            assert isinstance(right, dict)
            new_matches = { k: v.copy() for k, v in left.items() } #left.copy() alone doesn't cut it
            for k, v in right.items():
                if k in left:
                    new_matches[k].union(v)
                else:
                    new_matches[k] = v.copy()
            return new_matches
        else:
            return bool(left) or bool(right)


class disjunction(query):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def evaluate(self, ctx):
        left = self.left.evaluate(ctx)
        ctx = ctx.copy(matchvars=left)
        right = self.right.evaluate(ctx)
        #print((left, right))
        if isinstance(left, dict):
            #Match result
            assert isinstance(right, dict)
            new_matches = {} #{ k: v.copy() for k, v in left.items() } #left.copy() alone doesn't cut it
            for k, v in left.items():
                new_matches[k] = v
                if k in right:
                    new_matches[k].intersection(right[k])
            for k, v in right.items():
                if k not in left:
                    new_matches[k] = v
            return new_matches
            #subctx = ctx.copy(matchvars={})
            #left = self.left.evaluate(subctx)
            #subctx = ctx.copy(matchvars=left)
            #right = self.right.evaluate(subctx)
            #return right
        else:
            return bool(left) and bool(right)


class stringseq(query):
    def __init__(self, items):
        self.items = items

    def evaluate(self, ctx):
        return ''.join((i if isinstance(i, str) else i.evaluate(ctx) for i in self.items))


class variable(query):
    def __init__(self, name):
        self.name = name
        self.cached_possible_values = None

    def evaluate(self, ctx):
        return ctx.extras['match_possible_values'][self.name]


class constant(query):
    def __init__(self, name):
        self.name = name

    def evaluate(self, ctx):
        return ctx.variables[self.name]

class negation(query):
    def __init__(self, right):
        self.right = right

    def evaluate(self, ctx):
        return not bool(self.right.evaluate(ctx))


class funccall(query):
    def __init__(self, name, arglist):
        self.name = name
        self.arglist = arglist

    def evaluate(self, ctx):
        if self.name == '?':
            #It's the match function
            passed_args = [ ctx.matchvars.get(a.name) if isinstance(a, variable) else (None if a == '*' else a) if isinstance(a, str) else a.evaluate(ctx) for a in self.arglist ]
            #passed_args = [ None if a == '*' or isinstance(a, variable) else a if isinstance(a, str) else a.evaluate(ctx) for a in self.arglist ]
            #passed_args = { k: v for (k, v) in zip(('origin', 'rel', 'target'), passed_args) }
            result = {}
            for link in ctx.model.multimatch(*passed_args):
                if isinstance(self.arglist[0], variable):
                    result.setdefault(self.arglist[0].name, set()).add(link[0])
                if isinstance(self.arglist[1], variable):
                    result.setdefault(self.arglist[1].name, set()).add(link[1])
                if isinstance(self.arglist[2], variable):
                    result.setdefault(self.arglist[2].name, set()).add(link[2])
            return result
        else:
            raise NotImplementedError
