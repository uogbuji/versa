# Versa Literate

The JSON representation of Versa is good for data exchange and other
programming uses, but data on the Web and in KGs is often managed by
people who need a friendlier means of expression. Versa Literate is a
language based on [Markdown](http://daringfireball.net/projects/markdown/) for Web data in Versa form.
A basic representation equivalent to the link set in the [introductory section](https://github.com/uogbuji/versa/blob/master/doc/index.md) follows.

    # @docheader
    
    * @base: http://uche.ogbuji.net
    * @prop-base: http://www.w3.org/TR/html5/
    
    # /ndewo/ [web-page]
    
    * title: "Ndewo, Colorado"
    * link-type/author: </>
        * link/description: "Uche Ogbuji"
    * link-type/see-also: <http://www.goodreads.com/book/show/18714145-ndewo-colorado>
        * link/label: "Goodreads"
    
    # /
    
    * link-type/see-also: </ndewo/>

Links are given from two different origins, marked using the
Markdown convention for a header `"# "`. Relationships from
each origin are given as an unordered list in the form `relationship: target`.
Link attributes, if any, are given in a sublist.

The above uses several abbreviation mechanisms, particularly to reduce
the visual load of IRIs. Unabreviated, it would look as follows.

    # http://uche.ogbuji.net/ndewo/
    
    * <http://purl.org/versa/type>: <http://purl.org/versa/type/web-page>
    * <http://www.w3.org/TR/html5/title>: "Ndewo, Colorado"
    * <http://www.w3.org/TR/html5/link-type/author>: <http://uche.ogbuji.net/>
        * <http://www.w3.org/TR/html5/link/description>: "Uche Ogbuji"
    * <http://www.w3.org/TR/html5/link-type/see-also>: <http://www.goodreads.com/book/show/18714145-ndewo-colorado>
        * <http://www.w3.org/TR/html5/link/label>: "Goodreads"
    
    # http://uche.ogbuji.net/
    
    * <http://www.w3.org/TR/html5/link-type/see-also>: <http://uche.ogbuji.net/ndewo/>




# TODO: More expansive example. Maybe expand on following skeleton



    # @docheader
    
    * @uri:
	    * @base: http://uche.ogbuji.net
	    * @schema: http://www.w3.org/TR/html5/
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

