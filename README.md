# Versa

Versa is a model for Web resources and relationships. It has a lot in common
with Resource Description Framework (RDF) or Property Graphs (PG). It is
a way to express and work with data on the Web, in direct terms of resources
and rich linking between these resources. This also makes it a good and
natural way to exrpess Knowledge Grapgs (KG).

This repository provides specification as well as tools for using Versa in
practice, and which serve as reference implementations.

# Brief introduction to Versa

To get a simple idea of Versa, think about how you can express the relationship
between a Web page and its author in HTML5. 

    <a href="http://uche.ogbuji.net" rel="author">Uche Ogbuji</a>
    
Let's say the page being described is `http://uche.ogbuji.net/ndewo/`.
Versa makes it easy to pull together all these author link components into a single construct for easy understanding and manipulation.

    http://uche.ogbuji.net/ndewo/   author  http://uche.ogbuji.net  (caption="Uche Ogbuji")

In Versa this is called a link, and a link has four basic components, an
origin, a relationship, a target and a set of attributes. Link relationships
(also known as link types) are critical because they place links in context,
and Versa expects relationships to be IRIs so the context (meaning, if you like)
is properly expressed and fully scoped. Since rel=author is defined in HTML5,
you can complete the above as follows (using a made-up IRI for sake of example):

    http://uche.ogbuji.net/ndewo/   http://www.w3.org/TR/html5/link-type/author  http://uche.ogbuji.net  (caption="Uche Ogbuji")

You can express Versa links in JSON, for example:

    ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/author", "http://uche.ogbuji.net", {"caption": "Uche Ogbuji"}]

Usually you think of links in groups, ro example the many links from one page,
or all the various links across, out of and into a Web site. Versa is
designed for working with such collections of links. A collection of links
in Versa is called a linkset. Again you can express a linkset in JSON.

    [
        ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/author", "http://uche.ogbuji.net", {"http://www.w3.org/TR/html5/link/caption": "Uche Ogbuji"}],
        ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/see-also", "http://www.goodreads.com/book/show/18714145-ndewo-colorado", {"http://www.w3.org/TR/html5/link/label": "Goodreads"}],
        ["http://uche.ogbuji.net/", "http://www.w3.org/TR/html5/link-type/see-also", "http://uche.ogbuji.net/ndewo/"]
    ]

Notice that the third link has no attributes. Attributes are optional. I
invented a `see-also` relationship to represent a simple HTML link with no
`rel` attribute. The second link captures the idea of an HTML `alt`
attribute with a label attribute. In fact, HTML defines a bunch of
attributes which can be used with links, and you can add your own using XML
namespaces or HTML5 data attributes. This is why attributes are a core part
of a link in Versa. A Web link ties together multiple bits of information
in an extensible way, and attributes provide the extensibility, ensuring you
can work with all these bits of information as a unit.

If you think about data on the Web, links from one resource to another are
useful, but it's also useful to be able to express simple properties of a
resource. Versa supports this in the form of what's called a data link.
For example you could capture the title and other metadata about a resource.

    ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/title", "Ndewo, Colorado"]

The target of a data link is not a Web resource but rather a simple piece of
information. Technically, in Versa syntax you should always signal resources
as IRIs. In Javascript form this looks as follows:

    [
        ["<http://uche.ogbuji.net/ndewo/>", "<http://www.w3.org/TR/html5/link-type/author>", "<http://uche.ogbuji.net>", {"<http://www.w3.org/TR/html5/link/description>": "Uche Ogbuji"}],
        ["<http://uche.ogbuji.net/ndewo/>", "<http://www.w3.org/TR/html5/link-type/see-also>", "<http://www.goodreads.com/book/show/18714145-ndewo-colorado>", {"<http://www.w3.org/TR/html5/link/label>": "Goodreads"}],
        ["<http://uche.ogbuji.net/>", "<http://www.w3.org/TR/html5/link-type/see-also>", "<http://uche.ogbuji.net/ndewo/>"]
        ["<http://uche.ogbuji.net/ndewo/>", "<http://www.w3.org/TR/html5/title>", "Ndewo, Colorado"]
    ]

The angle brackets signal to Versa what should be treated as an IRI.
Versa origins and relationships are always IRIs, so you can omit the angle
brackets in those cases.

    [
        ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/author", "<http://uche.ogbuji.net>", {"<http://www.w3.org/TR/html5/link/description>": "Uche Ogbuji"}],
        ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/see-also", "<http://www.goodreads.com/book/show/18714145-ndewo-colorado>", {"<http://www.w3.org/TR/html5/link/label>": "Goodreads"}],
        ["http://uche.ogbuji.net/", "http://www.w3.org/TR/html5/link-type/see-also", "<http://uche.ogbuji.net/ndewo/>"]
        ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/title", "Ndewo, Colorado"]
    ]

All Versa data link targets are represented as strings, but they can be
interpreted as e.g. numbers, dates or other data types. Attributes are
useful for signaling such interpretation.

    ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/created", "2013-09-01", {"<@type>", "<@datetime>"}]

Notice the syntax used in the attribute. Versa provides some common data
modeling primitives such as a way to express the interpreted type of a data
link target. `@type` is just a convenient abbreviation for referring
to this Versa built-in concept. You can write out this link in full as follows:

    ["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/created", "2013-09-01", {"<http://purl.org/versa/type>", "<http://purl.org/versa/datetime>"}]

# Developer notes

Dosctring style: [Google](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) + Markdown
