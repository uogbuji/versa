# Versa

Versa is a model for Web resources and relationships. If you're familiar with Resource Description Framework (RDF)
you can think of it as an evolution of RDF that's at once simpler and more expressive. If not, just think about
to as a way to express and work with data on the Web in a way that fits with how we think of the Web in terms of
resources and rich linking between these resources.

To get a simple idea of Versa, think about how you can express the relationship between a Web page and its author
in HTML5. 

    <a href="http://uche.ogbuji.net" rel="author">Uche Ogbuji</a>
    
Let's say the page being described is `http://uche.ogbuji.net/ndewo/`. Versa makes it easy to pull together all
these pieces of this author link into a single construct for easy understanding and manipulation.

    http://uche.ogbuji.net/ndewo/   author  http://uche.ogbuji.net  (description="Uche Ogbuji")

In Versa this is called a link, and a link has four basic components, an origin, a relationship, a target and a
set of attributes. Link relationships (also known as link types) are critical because they place links in context, and Versa expects relationships
to be IRIs so the context is fully scoped to the Web, Since rel=author is defined in HTML5, you can complete the above
as follows (using a made-up IRI for sake of example):

    http://uche.ogbuji.net/ndewo/   http://www.w3.org/TR/html5/link-type/author  http://uche.ogbuji.net  (description="Uche Ogbuji")

You can express Versa links in JSON, for example:

    ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/author", "http://uche.ogbuji.net", {"description": "Uche Ogbuji"}]

Usually you think of links in groups, ro example the many links from one page, or all the various links across, out of
and into a Web site. Versa is designed for working with such collections of links. A collection of links in Versa is
called a linkset. Again you can express a linkset in JSON.

    [
        ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/author", "http://uche.ogbuji.net", {"http://www.w3.org/TR/html5/link/description": "Uche Ogbuji"}],
        ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/see-also", "http://www.goodreads.com/book/show/18714145-ndewo-colorado", {"http://www.w3.org/TR/html5/link/label": "Goodreads"}],
        ["http://uche.ogbuji.net/", "http://www.w3.org/TR/html5/link-type/see-also", "http://uche.ogbuji.net/ndewo/"]
    ]

Notice that the third link has no attributes. Attributes are optional. I invented a `see-also` relationship to
represent a simple HTML link with no `rel` attribute. The second link captures the idea of an HTML `alt` attribute
with a label attribute. In fact, HTML defines a bunch of attributes which can be used with links, and you can
add your own using XML namespaces or HTML5 data attributes. This is why attributes are a core part of a link in
Versa. A Web link ties together multiple bits of information in an extensible way, and attributes provide the
extensibility, ensuring you can work with all these bits of information as a unit.

If you think about data on the Web, links from one resource to another are useful, but it's also useful to be able
to express simple properties of a resource. Versa supports this in the form of what's called a data link.
For example you could capture the title and other metadata about a resource.

    ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/title", "Ndewo, Colorado"]

The target of a data link is not a Web resource but rather a simple piece of information. Technically, in Versa syntax
you should always signal resources as IRIs. In Javascript form this looks as follows:

    [
        ["<http://uche.ogbuji.net/ndewo/>", "<http://www.w3.org/TR/html5/link-type/author>", "<http://uche.ogbuji.net>", {"<http://www.w3.org/TR/html5/link/description>": "Uche Ogbuji"}],
        ["<http://uche.ogbuji.net/ndewo/>", "<http://www.w3.org/TR/html5/link-type/see-also>", "<http://www.goodreads.com/book/show/18714145-ndewo-colorado>", {"<http://www.w3.org/TR/html5/link/label>": "Goodreads"}],
        ["<http://uche.ogbuji.net/>", "<http://www.w3.org/TR/html5/link-type/see-also>", "<http://uche.ogbuji.net/ndewo/>"]
        ["<http://uche.ogbuji.net/ndewo/>", "<http://www.w3.org/TR/html5/title>", "Ndewo, Colorado"]
    ]

The angle brackets signal to Versa what should be treated as an IRI. Versa origins and relationships are always
IRIs, so you can omit the angle brackets in those cases.

    [
        ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/author", "<http://uche.ogbuji.net>", {"<http://www.w3.org/TR/html5/link/description>": "Uche Ogbuji"}],
        ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/see-also", "<http://www.goodreads.com/book/show/18714145-ndewo-colorado>", {"<http://www.w3.org/TR/html5/link/label>": "Goodreads"}],
        ["http://uche.ogbuji.net/", "http://www.w3.org/TR/html5/link-type/see-also", "<http://uche.ogbuji.net/ndewo/>"]
        ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/title", "Ndewo, Colorado"]
    ]

All Versa data link targets are represented as character sequences (i.e. "strings") but they can be interpreted
as e.g. numbers, dates or other data types. Attributes are useful for signaling such interpretation.

    ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/created", "2013-09-01", {"<@type>", "<@datetime>"}]

Notice the syntax used in the attribute. Versa provides some common data modeling primitives such as a way to
express the interpreted type of a data link target. `@type` is just a convenient abbreviation for referring
to this Versa built-in concept. You can write out this link in full as follows:

    ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/created", "2013-09-01", {"<http://purl.org/versa/type>", "<http://purl.org/versa/datetime>"}]


## Versa Literate

The JSON representation of Versa is good for data exchange and other programming uses, but data on the Web is often
managed by people, who need a friendlier means of expression. Versa Literate is a language based on [Markdown](http://daringfireball.net/projects/markdown/)
for Web data in Versa form. A basic representation equivalent to the above link set is as follows.

    # http://uche.ogbuji.net/ndewo/
    
    * <http://www.w3.org/TR/html5/title>: "Ndewo, Colorado"
    * <http://www.w3.org/TR/html5/link-type/author>: <http://uche.ogbuji.net/>
        * <http://www.w3.org/TR/html5/link/description>: "Uche Ogbuji"
    * <http://www.w3.org/TR/html5/link-type/see-also>: <http://www.goodreads.com/book/show/18714145-ndewo-colorado>
        * <http://www.w3.org/TR/html5/link/label>: "Goodreads"
    
    # http://uche.ogbuji.net/
    
    * <http://www.w3.org/TR/html5/link-type/see-also>: <http://uche.ogbuji.net/ndewo/>

Links are given from two different origins, marked using the Markdown convention for a header `"# "`. Relationships from
each origin are given as a list in the form `relationship: target`. Link attributes, if any, are given in a sublist.
As is the above is not a lot friendlier than the JSON version, but there are many abbreviations which make Versa
Literate much more readable. The following example uses several abbreviation mechanisms to express the same link set as the above.

    # @docheader
    
    * @base: http://uche.ogbuji.net
    * @prop-base: http://www.w3.org/TR/html5/
    
    # /ndewo/
    
    * title: "Ndewo, Colorado"
    * link-type/author: </>
        * link/description: "Uche Ogbuji"
    * link-type/see-also: <http://www.goodreads.com/book/show/18714145-ndewo-colorado>
        * link/label: "Goodreads"
    
    # /
    
    * link-type/see-also: </ndewo/>


Use of variables

    # @docheader
    
    * @uri:
	    * @base: http://uche.ogbuji.net
	    * @property: http://www.w3.org/TR/html5/
		* @resource: http://uche.ogbuji.net
	    * sch: http://schema.org
	    * rdf: http://www.w3.org/1999/02/22-rdf-syntax-ns
	    * rdfs: http://www.w3.org/2000/01/rdf-schema
	    * eg1: http://example.org/hello#
    * @prop-base: http://www.w3.org/TR/html5/
    
    # /ndewo/
    
    * title: "Ndewo, Colorado"
    * @rdf#label: "Ndewo, Colorado"
    * @sch/author: </>
        * link/description: "Uche Ogbuji"
    * @eg1@twitter-feed: <http://twitter.com/uogbuji>
    * see-also: uche@eg2
    * link-type/see-also: <http://www.goodreads.com/book/show/18714145-ndewo-colorado>
        * link/label: "Goodreads"
    
    # /
    
    * link-type/see-also: </ndewo/>




