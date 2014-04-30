<!-- Based on example at http://schema.org/CreativeWork -->

# @docheader

* @base: http://example.org/classics/      <!-- Because of this avatar-movie is resolved to http://example.org/movies/avatar-movie etc. -->
* @resource-type-base: http://schema.org/  <!-- Because of this Movie is resolved to http://schema.org/Movie etc. -->
* @property-base: http://schema.org/       <!-- Because of this name is resolved to http://schema.org/name etc. -->

# catcher-in-the-rye [Book]

* name: The Catcher in the Rye
* image: <catcher-in-the-rye-book-cover.jpg>
* bookFormat: <http://schema.org/Paperback>
* author: <http://example.org/author/jd_salinger.html>
* aggregateRating: <[AggregateRating]>
    * ratingValue: 4
    * reviewCount: 3077
* offers: <[Offer]>
    * price: $6.99
    * priceCurrency: USD
    * availability: <http://schema.org/InStock>
* numberOfPages: 224
* publisher: Little, Brown, and Company
* datePublished: 2006-05-04
* inLanguage: en
* isbn: 0316769487
* review: <[Review]>
    * reviewRating: 5
    * name: A masterpiece of literature
    * author: John Doe
    * datePublished: 2006-05-04
    * reviewBody: I really enjoyed this book. It captures the essential challenge people face as they try make sense of their lives and grow to adulthood.
* review: <[Review]>
    * reviewRating: 4
    * name: A good read.
    * author: Bob Smith
    * datePublished: 2006-06-15
    * reviewBody: Catcher in the Rye is a fun book. It's a good book to read.

