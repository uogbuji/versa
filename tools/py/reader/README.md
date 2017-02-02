

#RDFa Lite example

```
import urllib
import rdflib
from versa.reader import rdfalite
from versa.reader.rdfalite import DEFAULT_PREFIXES

g = rdflib.Graph()
for k, v in DEFAULT_PREFIXES.items():
    g.bind(k, v)

PAGE = 'http://link.houstonlibrary.org/portal/Half-of-a-yellow-sun-Chimamanda-Ngozi/n7KqqbZFJuM/'

with urllib.request.urlopen(PAGE) as fp:
    rdfalite.tordf(fp, g, PAGE)

#At this point g has the triples
len(g) # => 358
```

