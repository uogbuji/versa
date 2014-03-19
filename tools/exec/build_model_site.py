#!/usr/bin/env python

#FIXME: Alright already! Update to use Jinja2

import os
import re

#pip install amara==2.0.0a6
from amara import bindery
from amara.lib import U, inputsource
from amara.lib.iri import absolutize

LINK_PAT = re.compile('@(\w+)')

T0 = '''<!DOCTYPE html>
<html lang="en">
  
  <head>
    <title>BIBFRA.ME :: New Bibliographic Framework - Vocabulary</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <link href="{base}/css/bootstrap.css" rel="stylesheet" />
    <link href="{base}/css/bootstrap-responsive.css" rel="stylesheet" />
    <link href="{base}/css/style.css" rel="stylesheet" />
    
    <script type="text/javascript" src="{base}/js/jquery.js"></script>
    <script type="text/javascript" src="{base}/js/bootstrap.min.js"></script>

    <script type="text/javascript">
      $(".collapse").collapse()
    </script>
  </head>
  
  <body>
    
    <div class="navbar navbar-fixed-top">

      <div class="navbar-inner">

        <div class="container">
          <a class="brand" href="/">BIBFRA.ME
            <span class="tagline">
              <span style="padding-left: 20px; font-size: 70%; color: grey;">New Bibliographic Framework</span>
            </span>
          </a> 
      
          <ul class="nav pull-right">
            <li><a href="#">Overview</a></li>
            <li class="active"><a href="/vocab/">Vocabulary</a></li>
            <li><a href="/demos/">Demos</a></li>
            <li><a href="/library/">Library</a></li>
            <li><a href="/contribute/">Contribute</a></li>
            <li class="divider-vertical"></li>
            <li>
              <form class="navbar-search pull-right">
                <input type="text" class="search-query" placeholder="Search">
              </form>
            </li>
          </ul>
          
        </div>

      </div>
    </div>
    
    <div class="body container-fluid">

      <div class="this-nav row-fluid">
        <div class="span12" style="margin-top: 50px;">
          <ul class="breadcrumb">
            <li><a href = "/">Home</a> <span class="divider">/</span></li>
            <li><a href = "/vocab/">Vocab</a> <span class="divider">/</span></li>
{breadcrumbs}
          </ul>
        </div>
      </div>

      <div class="this row-fluid">
        <div class="span12">
          <h1 class="this-name">{clslabel}</h1>
          <h3 class="this-description">{clstag}</h3>
          <br />
        </div>
      </div>

      <div class="well">

      <div class="vocabulary-display">

{tables}

      </div> <!-- vocabulary-display -->
  
      </div>

      <div id="types" class="specific-types-display">

        <div class="row-fluid">
         <div class="span12">

          <h3 class="specific-types-text">More specific types</h3>

      <ul class="list well">
{specifictypes}
      </ul>
      
    </div>

  </div>

      </div> <!-- specific-types-display -->

    </div> <!-- container-fluid -->
 
    <!-- Modal -->

    <div class="modal hide" id="myModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">x</button>
        <h3 id="myModalLabel">Notes</h3>
      </div>
      <div class="modal-body">
      </div>
      <div class="modal-footer">
        <button class="btn" data-dismiss="modal" aria-hidden="true">Close</button>
      </div>
    </div>   
  
    <div class="footer">
      <div class="container">
        <p>BIBFRA.ME is a collaborative effort of <a href = "http://loc.gov/">US Library of Congress</a>, <a href="http://zepheira.com/">Zepheira</a> and <a href = "/contribute/">you!</a></p>
      </div>
    </div>

  </body>
</html>
'''#.format(vocabulary_display_sections)


T1 = '''        <div class="row-fluid vocabulary-display-section">
      
      <div class="span12">
        
        <div class="section-text parent">{0}{1}</div>
        
        <table class="table table-striped table-bordered">
          <thead>
                <tr>
        <th class="span2">Property</th>
        <th class="span2">Expected Value</th>
        <th class="span6">Description</th>
        <th class="span2">Related MARC Code</th>
        <th class="span2">Related RDA Code</th>
                </tr>
          </thead>
              <tbody>

{2}

              </tbody>
            </table>
        
      </div> <!-- span12 -->
      
    </div> <!-- vocabulary-display-section -->
'''#.format(properties)


T2 = '''\
          <tr id="{0}">
            <td>{0}{1}{2}{3}</td>
            <td>{4}</td>
            <td>{5}</td>
            <td>{6}</td>
            <td>{7}</td>
          </tr>
'''


AT0 = '''<!DOCTYPE html>
<html lang="en">
  
  <head>
    <title>MARC21 :: Link Data Vocabulary</title>
  </head>
  
  <body>
  {0}
  </body>
</html>
'''#.format(annotations)


CLASSES = {}

def run(modelsource=None, output=None, base=''):
    modelsource = inputsource(modelsource)
    indoc = bindery.parse(modelsource)
    annotations = {}
    #First find the annotation files
    for annfile in indoc.model.annotations:
        #print modelsource.resolver.absolutize(U(annfile.path))
        anndoc = bindery.parse(modelsource.resolve(U(annfile.path), indoc.xml_base))
        for ann in anndoc.annotations.annotation:
            target = ann.on.split(u'/', 1)
            target_cls, target_prop = (target[0], None) if len(target) == 1 else target
            #Build the HTML from the children of the annotation element
            htmlfromchildren = ''.join([ a.xml_encode() for a in ann.xml_children ])
            annotations.setdefault((target_cls, target_prop), []).append(htmlfromchildren)

    #Collect all the property refinements
    refinements = {}
    for prop in indoc.xml_select(u'//*[@refines]'):
        prop.xml_parent()
        source_cls, source_prop = prop.xml_parent.id, prop.id
        target = prop.refines.split(u'/', 1)
        #Target class is the same as source if not specified
        target_cls, target_prop = (source_cls, target[0]) if len(target) == 1 else target
        refinements.setdefault((target_cls, target_prop), []).append((source_cls, source_prop))

    #Build a graph of the classes
    for cls in indoc.model.class_:
        CLASSES[cls.id] = (cls, U(cls.isa).split() if cls.isa else [])

    #Now fix up all the parents, replacing IDs with the actual XML
    for clsid, (cls, parents) in CLASSES.items():
        parents = [ CLASSES[p][0] for p in parents ]
        CLASSES[clsid] = (cls, parents)

    def handle_inline_links(text):
        '''
        Transform that takes inline links and expands them
        '''
        def replace(match):
            eid = match.group(1)
            return '<a href="{0}/{1}/index.html">{2}</a>'.format(base, eid, CLASSES[eid][0].label)
        return LINK_PAT.sub(replace, text)


    #Now build the pages
    for clsid, (maincls, parents) in CLASSES.items():
        ancestors = []
        def add_ancestors(cls):
            for p in CLASSES[cls.id][1]:
                add_ancestors(p)
            ancestors.append(cls)
            return
        add_ancestors(maincls)
        basedir = os.path.join(output, U(maincls.id).encode('utf-8'))
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        outf = open(os.path.join(basedir, 'index.html'), 'w')

        class_chunks = []
        breadcrumb_chunks = []

        #Iterate over each ancestor class to inherit properties
        #for outcls in ancestors + [maincls]:
        for outcls in ancestors:
            property_chunks = []

            #Check for reference to annotations at class level
            ann_html = ''
            if (outcls.id, None) in annotations:
                #ann_html = ' <a class="notes" data-toggle="modal" href="notes.html#{0}" data-target="#myModal">[*]</a>\n'.format(U(outcls.id))
                ann_html = ' <button class="btn btn-mini notes" data-toggle="modal" href="notes.html" data-target="#myModal"><i class="icon-comment"></i></button>\n'.format(U(outcls.id))

            for prop in (outcls.property or []):
                typedesc = handle_inline_links(U(prop.typedesc))
                description = handle_inline_links(U(prop.description))

                #Check for reference to annotations at property level
                prop_ann_html = ''
                if (outcls.id, prop.id) in annotations:
                    #prop_ann_html = ' <a class="notes" data-toggle="modal" href="notes.html#{0}.{1}" data-target="#myModal">[*]</a>\n'.format(outcls.id, prop.id)
                    prop_ann_html = ' <button class="btn btn-mini notes" data-toggle="modal" href="notes.html" data-target="#myModal"><i class="icon-comment"></i></button>\n'.format(outcls.id, prop.id)

                #Check for refinements of the property
                prop_refines_html = ''
                if prop.refines:
                    continue

                #if prop.refines:
                #    target = prop.refines.split(u'/', 1)
                #    target_cls, target_prop = (None, target[0]) if len(target) == 1 else target
                #    #FIXME: Add integrity check
                #    if target_cls:
                #        prop_refines_html = '<br> (refines <a href="../{0}/index.html">{1}</a>)\n'.format(target_cls, prop.refines)
                #    else:
                #        prop_refines_html = '<br> (refines {0})\n'.format(prop.refines)

                prop_refinements_html = ''
                refs = refinements.get((outcls.id, prop.id))
                if refs:
                    refs_html = ''.join(['<tr><td>{0}</td></tr>'.format(source_prop if outcls.id == source_cls else source_cls + '/' + source_prop) for (source_cls, source_prop) in refs])
                    prop_refinements_html = '''\
                <button type="button" class="btn btn-mini" data-toggle="collapse" data-target="#refine-{0}"><i class="icon-plus"></i></button>

                <div id="refine-{0}" class="collapse">
                    <table class="table">
                         {1}
                    </table>
                </div>'''.format(U(prop.label), refs_html)

                property_chunks.append(T2.format(
                    U(prop.label),
                    prop_ann_html,
                    prop_refines_html,
                    prop_refinements_html,
                    typedesc,
                    description,
                    U(prop.marcref),
                    U(prop.rdaref)))

            header = 'Properties from <A href="../{0}/index.html">{1}</a>'.format(U(outcls.id), U(outcls.label))
            class_chunks.append(T1.format(header, ann_html, ''.join(property_chunks)))
            if outcls == maincls:
                breadcrumb_chunks.append('<li class="active">{0}</li>'.format(U(outcls.label)))
            else:
                breadcrumb_chunks.append('<li><a href="../{0}/index.html">{1}</a> <span class="divider">/</span></li>'.format(U(outcls.id), U(outcls.label)))

        childclasses = [ cls for (clsid, (cls, parents)) in CLASSES.items() if maincls in parents ]

        specific_chunks = [ '<li><a href="../{0}/index.html">{1}</a></li>\n'.format(U(cls.id), U(cls.label)) for cls in childclasses ]

        outf.write(T0.format(
            base=base,
            breadcrumbs=''.join(breadcrumb_chunks),
            clslabel=maincls.label,
            clstag=maincls.tagline,
            tables=''.join(class_chunks),
            specifictypes=(''.join(specific_chunks if specific_chunks else '(None)')),
            ))

        outf.close()

        #Write annotations file
        current_annotations = []
        for outcls in ancestors:
            #Is there an annotation for this class?
            if (outcls.id, None) in annotations:
                #Build the accumulated HTML annotations into one chunk
                htmlchunk = '\n'.join(annotations[(outcls.id, None)])
                #Then format it for the notes.html
                ann_html = '<div class="annotations"><a class="annotationTitle" name="{0}">{0}</a>{1}</div>\n'.format(U(outcls.id), htmlchunk)
                current_annotations.append(ann_html)
            #Is there an annotation for any of its properties?
            for prop in (outcls.property or []):
                if (outcls.id, prop.id) in annotations:
                    #Build the accumulated HTML annotations into one chunk
                    htmlchunk = '\n'.join(annotations[(outcls.id, prop.id)])
                    #Then format it for the notes.html
                    ann_html = '<div class="annotations"><a class="annotationTitle" name="{0}.{1}">{0}.{1}</a>{2}</div>\n'.format(U(outcls.id), prop.id, htmlchunk)
                    current_annotations.append(ann_html)

        if current_annotations:
            annf = open(os.path.join(basedir, 'notes.html'), 'w')
            annf.write(AT0.format('\n'.join([ann for ann in current_annotations])))
            annf.close()


if __name__ == '__main__':
    from akara.thirdparty import argparse #Yes! Yes! Import not at top
    #build_model.py --base=/vocab doc/bibframe.xml /tmp/bibframe
    parser = argparse.ArgumentParser()
    #parser.add_argument('-o', '--output')
    parser.add_argument('model', metavar='source', help='The model file')
    #Don't let argparse convert to stream because we need the base URI
    #parser.add_argument('model', metavar='source', type=argparse.FileType('r'),
    #                    help='The model file')
    parser.add_argument('output_root', metavar='output_base',
                        help='Root directory for the output (will be created if not present)')
    parser.add_argument('-b', '--base', metavar="SITE_BASE_URL", dest="baseurl", default='',
                        help="Base URL for the generated site")
    args = parser.parse_args()
    run(modelsource=args.model, output=args.output_root, base=args.baseurl)
    #indoc = bindery.parse(sys.argv[1])
    #args.model.close()

