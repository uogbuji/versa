<!--- Based on example at https://schema.org/CreativeWork -->

# @docheader

* @iri:
    * @base: http://example.org/classics/
    * @schema: https://schema.org/

# catcher-in-the-rye [Book]

* name: The Catcher in the Rye
* image: <catcher-in-the-rye-book-cover.jpg>
* bookFormat: <https://schema.org/Paperback>
* numberOfPages: 224
* author: <jds>
* inLanguage: en
* isbn: 0316769487
* aggregateRating: 4
    * reviewCount: 3077
* publication:
    * publisher: lbc
    * date: 2006-05-04
* offer: <offer-1>
* review: <review-1>
* review: <review-2>

# jds [Person]

* name: J. D. Salinger
* birthDate: 1919-01-01

# offer-1 [Offer]

* price: 6.99
* priceCurrency: USD
* availability: <https://schema.org/InStock>

# lbc [Organization]

* name: Little, Brown, and Company

# review-1 [Review]

* rating: 5
* title: A masterpiece of literature
* author: John Doe
* datePublished: 2006-05-04
* body: I really enjoyed this book. It captures the essential challenge people face as they try make sense of their lives and grow to adulthood.

# review-2 [Review]

* rating: 4
* title: A good read.
* author: Bob Smith
* datePublished: 2006-06-15
* body: Catcher in the Rye is a fun book. It's a good book to read.
