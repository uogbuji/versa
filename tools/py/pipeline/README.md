This Versa pipeline library provides  a toolkit for constructing data transformation pipelines for Versa models.

# Overview and example

A Versa pipeline transforms one graph's patterns and vocabularies to another, based on a set of declared rules for pattern matching and output graph construction.

Take the following pair of graphs:

![Black Star graph](http://gonzaga.ogbuji.net/~uche/tech/2021/blackstar1.jpg)

The left hand side is the input graph, based on the [Black Star test example](https://raw.githubusercontent.com/uogbuji/versa/pipeline_uni/test/resource/schemaorg/blackstar.md), which is based on [Schema.org MusicAlbum](https://schema.org/MusicAlbum). The right hand is the output graph, based on the [MusicBrainz schema](https://musicbrainz.org/doc/MusicBrainz_Database/Schema).

Here is the input graph in Versa literate format:

```
<!-- 
# @docheader

* @iri:
    * @base: http://example.org/records/
    * @schema: https://schema.org/

# black-star [MusicAlbum]

* name: Mos Def & Talib Kweli Are Black Star
* byArtist: <md>
* byArtist: <tk>
* release:
    * catalogNumber: RWK 1158-2

# md [Person]

* name: Mos Def

# tk [Person]

* name: Talib Kweli
* ```
