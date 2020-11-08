from django import template
import math
register = template.Library()

@register.filter
def index(indexable, i):
    return indexable[i]

@register.filter
def gt(a, b):
    return a > b

@register.filter
def powOf2(a):
    return math.log(a, 2).isInteger()