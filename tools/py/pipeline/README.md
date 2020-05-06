# Versa pipeline

Tools for constructing data transformation pipelines for Versa models

## Overview

These tools provide a declarative means for expressing rules for
transformation one data dialect to another. For example, you might
have data expressed according to in the [Dublin Core Metadata Initiative](https://www.dublincore.org/specifications/dublin-core/dces/) and you want it remodeled as Schema.org.
Versa pipelines provide a framework for writing this conversion DC. The DC
could be received in the form of XML or RDF, and the Schema.org could be
intended for embedding as Microdata in HTML, but the Versa pipeline
focuses on conversion from one abstract model of Versa to another. You would
use a buiult-in or custom reader to create the input model, and use
a writer to serialize the output model.

Versa pipelines are implemented as a Python-based DSL, but the intended
semantics are declarative.


