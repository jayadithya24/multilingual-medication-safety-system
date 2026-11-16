from pathlib import Path
import fitz, re, json, shutil, urllib.request, zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'revised_reports'
OUT.mkdir(exist_ok=True)
SRC = Path('C:/Users/PC/.codex/attachments/f904730b-0069-48e3-97cb-2a39b0197464/Pasted text.txt')
DOWNLOADS = Path('C:/Users/PC/Downloads')

def inspect():
    for name in ['Report_Version1_MMSS', 'Report_Version2_GraphBased_DSS']:
        doc = fitz.open(DOWNLOADS / (name + '.pdf'))
        text = '\n'.join(f'\n=== PDF PAGE {i+1} ===\n{p.get_text()}' for i,p in enumerate(doc))
        (OUT / (name + '_original.txt')).write_text(text, encoding='utf-8')
        print(name, 'pages',len(doc))
        print('figures',[(i+1,len(p.get_images())) for i,p in enumerate(doc) if p.get_images()])
        print(text[:800])
    t=SRC.read_text(encoding='utf-8')
    (OUT/'original_source.tex').write_text(t,encoding='utf-8')
    for a,b in [(175,205),(235,298),(532,591),(1370,1456)]:
        print('\nSOURCE',a,b,'\n'+'\n'.join(t.splitlines()[a-1:b]))

def compiler():
    req=urllib.request.Request('https://api.github.com/repos/tectonic-typesetting/tectonic/releases/latest',headers={'User-Agent':'report-revision'})
    data=json.load(urllib.request.urlopen(req))
    assets=[a for a in data['assets'] if 'x86_64-pc-windows' in a['name'] and a['name'].endswith('.zip')]
    print([(a['name'],a['browser_download_url']) for a in assets])
    target=OUT/'compiler'; target.mkdir(exist_ok=True)
    urllib.request.urlretrieve(assets[-1]['browser_download_url'], target/'tectonic.zip')
    with zipfile.ZipFile(target/'tectonic.zip') as z: z.extractall(target)
    print('compiler ready',list(target.glob('*.exe')))

def assets():
    from PIL import Image, ImageOps, ImageDraw
    doc=fitz.open(DOWNLOADS/'Report_Version2_GraphBased_DSS.pdf')
    names=['vtu','sahyadri','architecture-diagram','modular-diagram','class-diagram','state-diagram','use-case-diagram','sequence-diagram','activity-diagram','dfd-level-0','dfd-level-1','medicine-scan','medicine-scan-result','voice-search','voice-search-result','knowledge-graph','safety-analysis','interaction-graph','disease-protocols','clinical-insights','journal-insights','doctor-account-request']
    xrefs=[]
    for p in doc:
        for image in p.get_images():
            if image[0] not in xrefs: xrefs.append(image[0])
    print('unique images',len(xrefs),'expected',len(names))
    fig=OUT/'fig';fig.mkdir(exist_ok=True)
    thumbs=[]
    for name,xref in zip(names,xrefs):
        obj=doc.extract_image(xref)
        target=fig/(name+'.'+obj['ext']);target.write_bytes(obj['image'])
        im=Image.open(target).convert('RGB')
        print(name,im.size,obj['ext'])
        thumb=Image.new('RGB',(400,300),'white'); thumb.paste(ImageOps.contain(im,(390,270)),(5,25));ImageDraw.Draw(thumb).text((5,5),name,fill='black');thumbs.append(thumb)
    sheet=Image.new('RGB',(1200,300*((len(thumbs)+2)//3)), '#dddddd')
    for i,thumb in enumerate(thumbs):sheet.paste(thumb,(i%3*400,i//3*300))
    sheet.save(OUT/'assets_contact_sheet.png')
    for i in [10,11,29,31,32,33,34,35,36,72,73]:
        doc[i].get_pixmap(matrix=fitz.Matrix(1,1)).save(OUT/f'original_page_{i+1}.png')
    d1=fitz.open(DOWNLOADS/'Report_Version1_MMSS.pdf')
    import difflib
    a='\n'.join(p.get_text() for p in d1);b='\n'.join(p.get_text() for p in doc)
    dif='\n'.join(difflib.unified_diff(a.splitlines(),b.splitlines(),n=1))
    (OUT/'version_differences.txt').write_text(dif,encoding='utf-8')
    print('differences',dif[:16000])

def prepare():
    t=SRC.read_text(encoding='utf-8')
    t=t.replace('\\usepackage{float}', '\\usepackage{float}\n\\usepackage{placeins}\n\\usepackage{needspace}')
    t=t.replace('\\usepackage{titlesec}', '\\usepackage{titlesec}\n\\titlespacing*{\\section}{0pt}{12pt plus 2pt}{6pt}\n\\titlespacing*{\\subsection}{0pt}{10pt plus 2pt}{4pt}\n\\usepackage{tocloft}\n\\renewcommand{\\cftsecfont}{\\small}\n\\renewcommand{\\cftsubsecfont}{\\small}\n\\renewcommand{\\cftsecpagefont}{\\small}\n\\renewcommand{\\cftsubsecpagefont}{\\small}\n\\setlength{\\cftbeforechapskip}{2pt}\n\\setlength{\\cftbeforesecskip}{0pt}\n\\setlength{\\cftbeforesubsecskip}{0pt}')
    # Number the bibliography in the same sequence used by Table 2.1.
    start=t.index('\\begin{thebibliography}{99}')
    end=t.index('\\end{thebibliography}',start)
    entries=re.findall(r'\\bibitem\{r(\d+)\}[^\n]*',t[start:end])
    assert len(entries)==30
    items=re.findall(r'\\bibitem\{r\d+\}[^\n]*',t[start:end])
    items.sort(key=lambda s:int(re.search(r'\\bibitem\{r(\d+)\}',s).group(1)))
    t=t[:start]+'\\begin{thebibliography}{99}\n'+'\n'.join(items)+'\n'+t[end:]
    # Compact front-matter lists without removing any figures.
    t=t.replace('\\tableofcontents','{\\small\\setstretch{1.0}\\tableofcontents}')
    t=t.replace('\\listoffigures','{\\small\\setstretch{1.0}\\listoffigures}')
    t=t.replace('\\listoftables','{\\small\\setstretch{1.0}\\listoftables}')
    short={
      'Medicine scanning interface for uploading or capturing a prescription or medicine strip.':'Medicine scanning interface',
      'Medicine identification result showing localised medicine information.':'Localised medicine identification result',
      'Voice-search interface with language selection, recording, and audio-upload controls.':'Multilingual voice-search interface',
      'Recognised medicine query and localised response.':'Recognised query and localised response',
      'Drug knowledge graph showing medicine, disease, and side-effect relationships.':'Medicine knowledge graph',
      'Safety-analysis interface showing a recorded drug interaction and severity.':'Drug interaction and severity result',
      'Interaction knowledge graph for a selected pair of medicines.':'Pairwise interaction graph',
      'Disease Protocols interface showing medicine records associated with a selected disease.':'Disease protocols',
      'Clinical Insights interface with a disease summary and linked medicine records.':'Clinical insights',
      'Curated journal and research references displayed by GMDSS.':'Journal and research references',
      'Doctor portal for submitting a doctor-account request for administrator approval.':'Doctor-account request interface',
      'Lookup pipeline. English queries skip the fallback step and go to ``Not found\'\' when no match exists.':'Medicine lookup pipeline',
      'Graph schema using the three relationship types accepted by the loader.':'Implemented knowledge-graph schema',
      'Doctor request and patient consent workflow.':'Doctor approval and patient consent workflow'
    }
    for full,brief in short.items():t=t.replace('\\caption{'+full+'}','\\caption['+brief+']{'+full+'}')
    # Replace raster diagrams by vector PDFs and enlarge them.
    a=t.index('\\chapter{System Analysis');b=t.index('\\chapter{Methodology',a)
    design=t[a:b]
    heights={'architecture-diagram':.43,'modular-diagram':.40,'class-diagram':.60,'state-diagram':.38,'use-case-diagram':.46,'sequence-diagram':.58,'activity-diagram':.46,'dfd-level-0':.34,'dfd-level-1':.56}
    design=re.sub(r'\\includegraphics\[[^\]]+\]\{([^}]+)\}',lambda m:'\\includegraphics[width=\\textwidth,height='+str(heights[Path(m.group(1)).stem])+'\\textheight,keepaspectratio]{'+Path(m.group(1)).stem+'.pdf}',design)
    design=design.replace('\\begin{figure}[htbp]','\\begin{figure}[H]')
    design=design.replace('\\begin{table}[htbp]','\\begin{table}[H]')
    design=design.replace('\\scalebox{0.75}','\\resizebox{0.97\\textwidth}{!}')
    design=design.replace('\\subsection{Entity--Relationship Model}','\\FloatBarrier\n\\Needspace{0.75\\textheight}\n\\subsection{Entity--Relationship Model}')
    design=design.replace('\\subsection{Collections and Graph Model}','\\FloatBarrier\n\\Needspace{0.68\\textheight}\n\\subsection{Collections and Graph Model}')
    for title,space in [('Class Diagram',.75),('State Diagram for Medication Scheduling',.68),('Use Case Diagram',.67),('Sequence Diagram',.82),('Activity Diagram',.68)]:
        design=design.replace('\\subsection{'+title+'}', '\\Needspace{'+str(space)+'\\textheight}\n\\subsection{'+title+'}')
    # DFD0 text follows the actual diagram rather than claiming absent actors.
    design=design.replace('as one process with three external entities and the external services','as one process receiving patient and doctor inputs and producing information and notifications')
    t=t[:a]+design+t[b:]
    t=t.replace('\\scalebox{0.62}', '\\scalebox{0.80}')
    t=t.replace('\\scalebox{0.8}', '\\scalebox{1.0}')
    t=t.replace('\\scalebox{0.72}', '\\scalebox{0.90}')
    # Chapter 8: retain original pixels, remove size caps that made text tiny.
    a=t.index('\\chapter{Results and Discussion}');b=t.index('\\section{Experimental Results}',a)
    results=t[a:b]
    results=re.sub(r'\\includegraphics\[[^\]]+\]',r'\\includegraphics[width=0.94\\textwidth,height=0.34\\textheight,keepaspectratio]',results)
    results=results.replace('\\begin{figure}[htbp]','\\begin{figure}[!htbp]')
    t=t[:a]+results+t[b:]
    a=t.index('\\chapter{Project Management}');b=t.index('\\chapter{Conclusion',a)
    management=t[a:b].replace('\\setstretch{1.75}','\\setstretch{1.5}')
    management=management.replace('\\begin{table}[htbp]','\\begin{table}[H]')
    management=management.replace('8 & Report writing & Alongside all phases & In progress','8 & Report writing & Final revision before submission & Completed')
    management=management.replace('M9 & Final report and demonstration & In progress','M9 & Final report completed for submission & Completed')
    management=management.replace('\\section{Milestones}','\\FloatBarrier\n\\Needspace{0.43\\textheight}\n\\section{Milestones}')
    management=management.replace('\\section{Work Breakdown Structure}','\\Needspace{0.58\\textheight}\n\\section{Work Breakdown Structure}')
    management=management.replace('\\section{Task Allocation and Individual Contribution}','\\FloatBarrier\n\\Needspace{0.38\\textheight}\n\\section{Task Allocation and Individual Contribution}')
    t=t[:a]+management+t[b:]
    # Moderate body spacing recovers room for readable figures; front matter,
    # tables and bibliography keep their own spacing.
    a=t.index('\\chapter{Introduction}')
    t=t[:a]+re.sub(r'\\setstretch\{1\.(?:35|4|5|55|65|75)\}',r'\\setstretch{1.30}',t[a:])
    t=t.replace('INTERACTS\\_WITH&Relationship', '\\shortstack[l]{INTERACTS\\_\\\\WITH}&Relationship')
    t=t.replace('|p{1.3cm}|p{8.4cm}|p{4.0cm}|', '|p{1.5cm}|p{8.2cm}|p{4.0cm}|')
    for version in [1,2]:
        v=t
        if version==1:
            v=v.replace('Graph-Based Multilingual Decision Support System for Medication Safety and Polypharmacy Risk Detection','Multilingual Voice-Assisted Medication Information and Safety Monitoring System')
            v=v.replace('GMDSS (Graph-Based Multilingual Decision Support System)','MMSS (Multilingual Medication Safety System)')
            v=v.replace('GMDSS','MMSS')
            v=v.replace('a graph-based multilingual decision support system for medication safety and polypharmacy risk detection','a multilingual, voice-assisted medication information and safety monitoring system')
            v=v.replace('A graph-based multilingual decision support system for medication safety','A multilingual, voice-assisted medication safety system')
            v=v.replace('a graph-based multilingual decision support system for ten common conditions','a multilingual, voice-assisted system for ten common conditions')
        name='Report_Version1_MMSS_Revised' if version==1 else 'Report_Version2_GraphBased_DSS_Revised'
        (OUT/(name+'.tex')).write_text(v,encoding='utf-8')
    print('Prepared both revised LaTeX files.')

def audit():
    report={}
    for p in OUT.glob('*_Revised.pdf'):
        doc=fitz.open(p)
        pages=[page.get_text() for page in doc]
        lof=[i+1 for i,t in enumerate(pages) if t.startswith('List of Figures')]
        table_pages=[i+1 for i,t in enumerate(pages) if 'Table 2.1:' in t]
        bibliography=[i+1 for i,t in enumerate(pages) if t.startswith('References') or re.search(r'\[30\].*Sutton',t,re.S)]
        entry_pages={}
        for term in ['Entity–Relationship Model','Entity--Relationship Model','Collections and Graph Model','10.3','10.4','Table 10.3:','Table 10.4:']:
            entry_pages[term]=[i+1 for i,t in enumerate(pages) if term in t and 'Table of Contents' not in t]
        text='\n'.join(pages)
        (OUT/(p.stem+'.txt')).write_text(text,encoding='utf-8')
        report[p.name]={'pages':len(doc),'list_of_figures_starts':lof,'literature_table_pages':table_pages,'bibliography_pages':bibliography,'section_pages':entry_pages,'unresolved_markers':text.count('??')}
        print(p.name,json.dumps(report[p.name],indent=2))
        for i,page in enumerate(doc):
            if any(term in pages[i] for term in ['System Architecture','Class Diagram','Entity–Relationship Model','Table 10.3:','Table 10.4:']) or i+1 in lof:
                page.get_pixmap(matrix=fitz.Matrix(1.1,1.1)).save(OUT/f'{p.stem}_check_{i+1}.png')
    (OUT/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

def package():
    summary=[]
    for name in ['Report_Version1_MMSS_Revised','Report_Version2_GraphBased_DSS_Revised']:
        doc=fitz.open(OUT/(name+'.pdf'))
        assert 75<=len(doc)<=80, (name,len(doc))
        pages=[p.get_text() for p in doc]
        text='\n'.join(pages)
        assert '??' not in text
        lof=next(i for i,t in enumerate(pages) if t.startswith('List of Figures'))
        assert pages[lof+1].startswith('List of Tables'), 'List of Figures spills over'
        assert len(re.findall(r'\b(?:5|6|8)\.\d+\b',pages[lof]))==24
        table=text[text.index('Table 2.1:'):]
        table=table[:table.index('Problems and Limitations of Existing Systems')]
        nums=list(map(int,re.findall(r'\[(\d+)\]',table)))
        assert nums==list(range(1,31)),nums
        refs='\n'.join(t for t in pages if t.startswith('References') or 'J. Leskovec' in t)
        nums=list(map(int,re.findall(r'\[(\d+)\]',refs)))
        assert nums==list(range(1,31)),nums
        er=next(t for t in pages if '5.5.1' in t and 'Conceptual ER model for application records' in t)
        assert er.index('5.5.1')<er.index('PATIENT')<er.index('Figure 5.10:')
        assert any('5.5.2' in t and 'Table 5.1:' in t and 'Table 5.2:' in t for t in pages)
        for number in [3,4]:
            assert any(f'10.{number}' in t and f'Table 10.{number}:' in t for t in pages)
        assert 'Report writing' in text and 'Final revision before' in text
        log=(OUT/(name+'.log')).read_text(encoding='utf-8')
        assert not any(s in log for s in ['Overfull','Missing character','undefined references','Float too large'])
        summary.append(f'{name}.pdf: {len(doc)} pages; all validation checks passed.')
    readme='''# Revised project reports

Both PDFs have 79 physical pages, including all front matter and references.

Changes applied to both versions:
- Table 2.1 and bibliography use matching reference numbers [1] through [30].
- The List of Figures fits on one page; all 24 figures are retained.
- Chapter 5 raster design diagrams are redrawn as scalable vector PDF graphics.
- The ER diagram and Chapter 6 vector figures are enlarged; Chapter 8 screenshots
  are included at larger sizes using their original embedded image pixels.
- Section 5.5.1 precedes the ER diagram, and 5.5.2 precedes both model tables.
- Chapter 10 report writing and the final-report milestone are Completed.
- Milestone and task-allocation headings precede their respective tables.
- Contents and heading spacing are compacted, with a 12pt report document class
  and the original A4 page margins retained. Body line spacing is 1.30.

## Build from LaTeX

Keep the `fig` directory beside the two `.tex` files. Compile with PDFLaTeX
(three passes for contents and cross-references), XeLaTeX, or Tectonic:

    tectonic Report_Version1_MMSS_Revised.tex
    tectonic Report_Version2_GraphBased_DSS_Revised.tex

The supplied PDFs were built with Tectonic 0.17.0 (XeTeX). A different TeX
distribution may paginate differently; check the 75–80 page limit after editing.
The vector assets are ready to use. `redraw_diagrams.py` is optional editable
drawing source; running it requires the Python reportlab package.
'''
    (OUT/'README.md').write_text(readme,encoding='utf-8')
    zip_path=OUT/'Revised_Reports_LaTeX_Source.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(OUT/'README.md','README.md')
        z.write(OUT/'validation.json','validation.json')
        for p in OUT.glob('*_Revised.tex'):z.write(p,p.name)
        t=(OUT/'Report_Version2_GraphBased_DSS_Revised.tex').read_text(encoding='utf-8')
        files=set(re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',t))
        for name in sorted(files):
            matches=[OUT/'fig'/name] if Path(name).suffix else list((OUT/'fig').glob(name+'.*'))
            matches=[p for p in matches if p.exists()]
            assert len(matches)==1,(name,matches)
            z.write(matches[0],'fig/'+matches[0].name)
        drawing=(ROOT/'tools/report_diagrams.py').read_text(encoding='utf-8')
        drawing=drawing.replace("Path(__file__).resolve().parents[1]/'docs/revised_reports/fig'", "Path(__file__).resolve().parent/'fig'")
        z.writestr('redraw_diagrams.py',drawing)
    print('\n'.join(summary))
    print('Packaged editable LaTeX and assets:',zip_path)

if __name__ == '__main__':
    import sys
    {'inspect':inspect,'compiler':compiler,'assets':assets,'prepare':prepare,'audit':audit,'package':package}[sys.argv[1]]()
