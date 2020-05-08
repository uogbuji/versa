# Versa pipeline

Tools for constructing data transformation pipelines for Versa models

# Overview

These tools provide a declarative means for expressing rules for
transformation one data dialect to another. For example, you might
have data expressed according to in the [Dublin Core Metadata Initiative](https://www.dublincore.org/specifications/dublin-core/dces/) and you want it remodeled as Schema.org.

Versa pipelines provide a framework for writing this conversion DC. The DC
could be received in the form of XML or RDF, and the Schema.org could be
intended for embedding as Microdata in HTML, but the Versa pipeline
focuses on conversion from one abstract model of Versa to another. You would
use a built-in or custom reader to create the input model, and use
a writer to serialize the output model.

This implementation of Versa pipelines is a Python-based DSL, but
the intended general semantics are declarative.

# Structure

A Versa pipeline starts with an input model and generates information in an
output model based on applied rules.

Versa pipelines have one or more phases. A usual initial phase is
fingerprinting, in which resources of interest are identified from the input
model. These can be given new IDs for their representation in the output
model, but a key focus of the fingerprinting phase is that input resources
which have been processed in the past can be identified, and the pipeline
design can determine how to deal with this. Such duplicated or elaborated
resources could be updated in place inthe output, for example.

The fingerprinting phase is typically followed by one or more transformation
phases in which the fingerprinted resources are mapped from the input
information to the output using a set of transformation rules.

There is shared state between the phases, called the interphase. It contains
operational information and metadata that needs to be shared between the
phases. For example the list of fingerprinted resources is usually stored
in the interphase.

# Operation

The rules are generally implemented as a collection of patterns to be matched
in the input model. When a pattern is matched it triggers one or more
action functions, which manipulate the data for the output model.

A simple example of how a pattern/action might look is the following mapping
entry (Python syntax):

    DUBLIN_CORE('title'): link(rel=SCHEMA_ORG('name'))

This says: when a link from a fingerprinted resource with a relationship
of `http://purl.org/dc/terms/title`, the way titles are expressed in the Dublin
Core vocabulary, is encountered in the input model, convert it into a link in
the output with the same metadata except for the relationship, which will be
changed to `https://schema.org/name`, the equivalent in Schema.org. The output
link origin will be as determined by the fingerprinting, the target, probably
a data value, will remain the same and so will any attributes. You can specify
rules to modify the origin, target or attributes as well in the `link` action
function.

Another common action function allows you to create new resources in the
output. See for example, the following excerpt from an input data model:

    * @schema: http://purl.org/dc/terms/

    # /things-fall-apart/ [Book]
    
    * title: "Things Fall Apart"
    * creator: "Chinua Achebe"

The creator is given as a simple string, but in many data applications it's
much better to treat a creator as a full resource. This allows you to, for
example deal with problems such as multiple names for the same person and
multiple people with the same name. In a Versa pipeline we might want to handle
this with a pattern/action such as:

    DUBLIN_CORE('creator'): materialize(SCH_NS('Person'),
                                        rel=SCHEMA_ORG('author'))
                                        unique=[
                                            (VTYPE_REL, SCH_NS('Person')),
                                            (SCH_NS('name'), target())
                                        ],
                                        links=[
                                            (SCH_NS('name'), target())
                                        ]

The `materialize` action function creates a resource in the output
model, representing the person entity implicit in that simple string
`"Chinua Achebe"`. The type is set to `https://schema.org/Person`.
As with the `link` action function a similar link is created in the output.
It goes from the origin set for the book through fingerprinting to the
materialized person resource as target, with `https://schema.org/author`
as the relationship.

The materialized person needs an IRI, and the `unique` parameter provides
input to the process of specifying the IRI. This could be something generated,
some existing ID looked up using the uniqueness parameters, or something else.
The `links` parameter also specifies a link from the materialized person,
In this case using the `https://schema.org/name` relationship, and using the
target value of the original input link.

A run from the above input model and using the example `link` and `materialize`
pattern/action mapping above might result in the following:

    * @schema: https://schema.org/

    # /things-fall-apart-NEWID/ [Book]
    
    * name: "Things Fall Apart"
    * author: /chinua-achebe-NEWID/

    # /chinua-achebe-NEWID/ [Person]
    * name: "Chinua Achebe"

# Context

Action functions use information provided in a context. The context includes,
for example, the input link that was encountered when the action function was
triggered. Action functions often interact with each other, and manipulate the
context between them.

The standard items in the context are as follows:

    * current link - link providing the basis for the local transforms to output processed in an action function
    * input model - Versa model providing the overall input to the transform
    * output model - Versa model holding the main output result of the transform
    * base IRI - reference base IRI, used resolve created resources into full IRIs, if specified in abbreviated form
    * variables - values that can be used to adjust aspects of data generated in the output model

