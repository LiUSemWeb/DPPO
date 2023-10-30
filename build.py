#!/usr/bin/env python3
from bs4 import BeautifulSoup, formatter
from glob import glob
import os
import re
import urllib.request
import zipfile
from pylode.profiles.vocpub import VocPub
import pdfkit
from rdflib import Graph


def copy_ontologies():
    """Copy ontologies to web path."""
    latest = {}

    # publish ontologies
    for source in sorted(glob("ontology/*/*/*", recursive=True)):
        if not source.endswith(".ttl"):
            continue
        
        print(f"Copy ontology {source}")

        parts = re.match("ontology/([^/]*)/([^/]*)", source)    
        name = parts.group(1)
        version = float(parts.group(2))
        base = f"docs/ontology/{name}/{version}/{name}"
        os.makedirs(f"docs/ontology/{name}/{version}/", exist_ok=True)
        g = Graph()
        g.parse(source)
        g.serialize(destination=f"{base}.ttl", format="turtle")
        g.serialize(destination=f"{base}.rdf", format="xml")
        g.serialize(destination=f"{base}.owl", format="xml")
        g.serialize(destination=f"{base}.jsonld", format="json-ld")
        
        if latest.get(name, 0) < version:
            latest[name] = version
        
    # add latest
    for name, version in latest.items():
        os.makedirs(f"docs/ontology/{name}/latest/", exist_ok=True)
        os.system(f"cp docs/ontology/{name}/{version}/* docs/ontology/{name}/latest/")


def download_owl2vowl():
    """Download and extract OWL2VOWL."""
    os.system("mkdir -p temp")
    path_to_jar = "temp/owl2vowl.jar"
    if not os.path.isfile(path_to_jar):
        path_to_zip = "temp/owl2vowl_0.3.7.zip"
        if not os.path.isfile(path_to_zip):
            url = "http://vowl.visualdataweb.org/downloads/owl2vowl_0.3.7.zip"
            urllib.request.urlretrieve(url, path_to_zip)

        with zipfile.ZipFile(path_to_zip, 'r') as zip_ref:
            zip_ref.extractall("temp/")


def build_pdf():
    """Convert docs to PDF using wkhtmltopdf."""
    try:
        html_formatter = formatter.HTMLFormatter(indent=4)
        
        for source in sorted(glob("ontology/*/*/*", recursive=True)):
            if not source.endswith(".ttl"):
                continue

            print(f"Generating PDF docs for {source}")

            parts = re.match("ontology/([^/]*)/([^/]*)", source)    
            name = parts.group(1)
            version = float(parts.group(2))
        

            html_file = f"docs/ontology/{name}/{version}/index.html"
            pdf_file = f"docs/ontology/{name}/{version}/{name}.pdf"
            
            # Drop TOC, logo and iframe before generating PDF 
            with open(html_file, encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                style = soup.new_tag('style', type='text/css')
                style.append("""
                    /* hack to avoid lonely heading (mot of the time at least) */
                    h2 {
                        page-break-inside: avoid;
                    }
                    .section h2::after {
                        content: "";
                        display: block;
                        height: 300px;
                        margin-bottom: -300px;
                    }
                    .entity {
                        page-break-inside: avoid;
                    }
                    p, dt, dd, ul {
                        margin-top: 10px;
                        margin-bottom: 10px;
                        padding-top: 0;
                        padding-bottom: 0;
                    }
                """)
                soup.head.append(style)
                
                for table in soup.select("table"):
                    table.insert(0, soup.new_tag("thead"))
                    table.wrap(soup.new_tag("tbody")).wrap(soup.new_tag("table"))
                    table.unwrap()
                    
                for id in ["toc", "pylode", "overview"]:
                    tag = soup.find(id=id)
                    if tag != None:
                        tag.decompose()
                
            pdfkit.from_string(soup.prettify(formatter=html_formatter), pdf_file, options = { "enable-local-file-access": "" })
    except Exception as e:
        print(e)
        print("PDF conversion cancelled. Is 'wkhtmltopdf' (https://wkhtmltopdf.org/) installed?")


def generate_vowl():
    """Generate VOWL specifications."""
    for source in sorted(glob("ontology/*/*/*", recursive=True)):
        if not source.endswith(".ttl"):
            continue
        
        print(f"Generating VOWL for {source}")

        parts = re.match("ontology/([^/]*)/([^/]*)", source)    
        name = parts.group(1)
        version = float(parts.group(2))
        
        os.makedirs(f"docs/webvowl/data/ontology/{name}/{version}/", exist_ok=True)
        # Note: The flag "add-opens" below fixes an issue with
        # "InaccessibleObjectException" in later versions of Java
        os.system(f"""
            java -Dlog4j.configurationFile=log4j2.xml \
                --add-opens java.base/java.lang=ALL-UNNAMED \
                -jar temp/owl2vowl.jar \
                -file {source} \
                -output docs/webvowl/data/ontology/{name}/{version}/{name}.json > /dev/null
        """)


def create_documentation():
    """Generate LODE documentation and instert VOWL visualization."""
    for source in sorted(glob("ontology/*/*/*", recursive=True)):
        if not source.endswith(".ttl"):
            continue
        
        print(f"Generating docs for {source}")

        parts = re.match("ontology/([^/]*)/([^/]*)", source)    
        name = parts.group(1)
        version = float(parts.group(2))
        os.makedirs(f"docs/ontology/{name}/{version}/", exist_ok=True)
                
        html_file = f"docs/ontology/{name}/{version}/index.html"
        od = VocPub(ontology=source)
        od.make_html(destination=html_file)

        # relative path to webvowl and vowl file
        path_to_webvowl = f"../../../webvowl/index.html#ontology/{name}/{version}/{name}"

        # # Insert overview section into documentation with WebVOWL in an iframe
        with open(html_file, encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            overview = BeautifulSoup(f"""
                <div id="overview" class="section">
                    <h2>Overview</h2>
                    <div class="figure">
                        <iframe id="iframe-overview" width="100%" height ="600px" src="{path_to_webvowl}"></iframe>
                        <div class="caption"><strong>Figure 1:</strong> Ontology overview</div>
                    </div>
                </section>
            """, "html.parser")
            tag = soup.find(id='metadata')
            tag.insert_after(overview)

            html_formatter = formatter.HTMLFormatter(indent=4)
            with open(html_file, "w") as f:
                f.write(soup.prettify(formatter=html_formatter))


                                        
def main():
    download_owl2vowl()
    generate_vowl()
    create_documentation()
    build_pdf()
    copy_ontologies()

if __name__ == "__main__":
    main()
