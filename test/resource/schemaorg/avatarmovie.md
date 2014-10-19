<!--- Based on http://schema.org/docs/gs.html#microdata_how -->

# @docheader

* @iri:
    * @base: http://example.org/movies/        <!--- Because of this avatar-movie is resolved to http://example.org/movies/avatar-movie etc. -->
    * @resource-type: http://schema.org/  <!--- Because of this Movie is resolved to http://schema.org/Movie etc. -->
    * @property: http://schema.org/       <!--- Because of this name is resolved to http://schema.org/name etc. -->
* @title: Avatar, the movie
* @interpretations:
    * label: @text
<!--- If the following are uncommented then you can omit "" from simple text values and <> from IRI values in the main resource descriptions
 * director: @resource
 * genre: @text
 * birthDate: @text -->

# avatar-movie [Movie]

* name: Avatar
* director: <james-cameron>
* trailer: <http://example.org/movies/avatar-theatrical-trailer.html>
* genre: "Science fiction"

# james-cameron [Person]

* name: James Cameron
* birthDate: "August 16, 1954" <!--- Notice the inclusion of closing ")" in the Schema.org example, which seems very odd -->

