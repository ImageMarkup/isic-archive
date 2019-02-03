#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import datetime

from bson import ObjectId
import dateutil.parser


def cast(value, typename):
    """Cast a value to a type, including special-purpose semantic processing for some values."""
    if typename is None:
        return value
    elif typename == 'objectid':
        return ObjectId(value)
    elif typename == 'integer':
        try:
            return int(value)
        except ValueError:
            return float('NaN')
    elif typename == 'number':
        try:
            return float(value)
        except ValueError:
            return float('NaN')
    elif typename == 'boolean':
        return bool(value) and value not in ['false', '0', 0, 'n']
    elif typename == 'string':
        return str(value)
    elif typename == 'date':
        if type(value) == int:
            return datetime.datetime.fromtimestamp(float(value) / 1000)
        else:
            return dateutil.parser.parse(value, default=datetime.datetime.fromtimestamp(0))
    else:
        raise ValueError('Illegal value for argument "typename": %s' % typename)


_mongo_operators = {
    'or': '$or',
    'and': '$and',
    'in': '$in',
    'not in': '$nin',
    '<=': '$lte',
    '<': '$lt',
    '>=': '$gte',
    '>': '$gt',
    '=': '$eq',
    '!=': '$ne',
}


def _astToMongo_helper(ast):
    """Convert a query language AST into an equivalent Mongo filter."""
    operator = ast['operator']
    operands = ast['operands']

    if operator in ['or', 'and']:
        left = _astToMongo_helper(operands[0])
        right = _astToMongo_helper(operands[1])

        return {_mongo_operators[operator]: [left, right]}
    elif operator == 'not':
        # Mongo knows how to invert certain operators, including the comparison
        # operators.
        if operands['operator'] in ['<=', '<', '>=', '>']:
            operator = operands['operator']
            field = operands['operands'][0]['identifier']
            value = operands['operands'][1]
            return {field: {'$not': {_mongo_operators[operator]: value}}}

        raise TypeError('_astToMongo_helper() cannot operate on an AST with not-nodes.')
    elif operator in ['in', 'not in', '<=', '<', '>=', '>', '=', '!=']:
        field = operands[0]['identifier']
        typename = operands[0].get('type')
        value = operands[1]

        if typename == 'objectid':
            value = map(lambda x: cast(x, 'objectid'), value)

        if operator in ['in', 'not in']:
            value = map(lambda x: None if x == '__null__' else x, value)

        if typename == 'boolean':
            value = map(lambda x: cast(x, 'boolean') if x is not None else x, value)

        return {field: {_mongo_operators[operator]: value}}


def _invert(ast):
    """Invert the polarity of a boolean expression."""
    operator = ast['operator']
    operands = ast['operands']

    if operator == 'not':
        # To invert a not expression, just remove the not.
        return _eliminate_not(operands)
    elif operator in ['and', 'or']:
        # For and/or expressions, apply DeMorgan's laws.
        new_operator = 'and' if operator == 'or' else 'or'
        new_operands = map(lambda x: {'operator': 'not', 'operands': x}, operands)

        return {'operator': new_operator, 'operands': map(_eliminate_not, new_operands)}
    elif operator in ['in', 'not in']:
        # For inclusion operators, just switch the one that was being used.
        return {'operator': 'in' if operator == 'not in' else 'not in', 'operands': operands}
    elif operator[0] in ['<', '>']:
        # For comparison operators, flip the operator around.
        new_operator = '<' if operator[0] == '>' else '>'
        if len(operator) == 1:
            new_operator += '='

        return {'operator': new_operator, 'operands': operands}
    else:
        # For equality operators, just switch the operator
        return {'operator': '=' if operator == '!=' else '!=', 'operands': operands}


def _eliminate_not(ast):
    """Eliminate all not-nodes in the AST by transforming their contents."""
    operator = ast['operator']
    operands = ast['operands']

    if operator in ['and', 'or']:
        # And/or expressions have two boolean operands that must be processed
        # recursively.
        return {'operator': operator, 'operands': map(_eliminate_not, operands)}
    elif operator in ['in', 'not in', '<=', '<', '>=', '>', '=', '!=']:
        # Operator expressions that work on constant values stay unchanged.
        return ast
    else:
        # Not expressions lose the not itself and invert the operand.
        if operands['operator'] in ['<=', '<', '>=', '>']:
            return ast
        return _eliminate_not(_invert(operands))


def astToMongo(ast):
    """Run the AST-to-mongo helper function after converting it to a not-free equivalent AST."""
    return _astToMongo_helper(_eliminate_not(ast))
