"""Clearly labelled procedural visual exhibits, with predeclared timelines."""
from PIL import Image, ImageDraw, ImageFont
from benchmark.util import ROOT, write_json
import random

SUSPECTS=['Nora Vale','Eli Stone','Maya Reed','Theo Park','Ada Finch']
COLORS=['teal','orange','purple','blue','red']

def font(size):
    for p in ['C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        try:return ImageFont.truetype(p,size)
        except OSError:pass
    return ImageFont.load_default()

def generate(seed):
    truths=[]
    for i in range(1,4):
        case=f'case_{i:02}';public=ROOT/'datasets'/'detective'/case/'public';(public/'images').mkdir(parents=True,exist_ok=True);(public/'documents').mkdir(exist_ok=True)
        responsible=SUSPECTS[i-1] if i<3 else None
        timeline=[{'time':'18:00','event':'Prototype present in laboratory','exhibits':['V02']},
            {'time':'18:10','event':'Nora entered east corridor','exhibits':['D01','V03']},
            {'time':'18:14','event':('Nora carried prototype case through east exit' if i==1 else 'Eli entered lab via service corridor' if i==2 else 'Two unidentified people entered unmonitored service corridor'),'exhibits':['V04','D01']},
            {'time':'18:18','event':'Prototype absent from laboratory','exhibits':['V05']}]
        truth={'case':case,'seed':seed+i,'responsible_person':responsible,'identifiable':i<3,'timeline':timeline,
            'visual_facts':{'V01':'East exit connects lab to corridor; service corridor is unmonitored','V02':'Prototype case on table at 18:00',
                'V03':'Teal coat at east corridor at 18:10','V04':('Teal coat carries silver case at east exit at 18:14' if i==1 else 'Orange coat carries silver case at service door; camera timestamp 18:19 has +5 minute offset' if i==2 else 'Two grey silhouettes; identities obscured; no distinguishing badge'),
                'V05':'Prototype table empty at 18:18','V06':'Blue coat in cafeteria at 18:12','V07':'Red coat at reception at 18:13',
                'V08':'Purple coat holds ordinary cardboard box at loading bay 18:11','V09':'Silver prototype case has black triangle marking',
                'V10':'Service door camera clock offset +5 minutes' if i==2 else 'Camera blind spot at service corridor'},
            'misleading_clues':['Motive in email is not proof','Maya cardboard box differs from silver prototype case'],
            'accepted_deductions':['Cross-reference coat identities and object marking','Correct camera offset before comparing timestamps'] if i<3 else ['Insufficient identity evidence; opportunity shared by multiple people'],
            'uncertainty':'Images are synthetic schematic exhibits; visual resemblance alone is not conclusive identity proof.'}
        # Establish truth BEFORE writing corresponding public evidence.
        write_json(ROOT/'evaluation_private'/'ground_truth'/(case+'.json'),truth);truths.append(truth)
        scenes=[('18:00','LAB','none','silver'),('18:10','EAST CORRIDOR','teal','none'),
            ('18:14' if i!=2 else '18:19','EAST EXIT' if i==1 else 'SERVICE DOOR','teal' if i==1 else 'orange' if i==2 else 'grey','silver' if i<3 else 'unknown'),
            ('18:18','LAB','none','none'),('18:12','CAFETERIA','blue','none'),('18:13','RECEPTION','red','none'),
            ('18:11','LOADING BAY','purple','cardboard'),('REFERENCE','OBJECT DETAIL','none','silver'),('MAINTENANCE','SERVICE CAMERA','none','none')]
        for j in range(1,11):
            image=Image.new('RGB',(960,600),'#e7eef4');d=ImageDraw.Draw(image)
            d.rectangle((0,0,960,80),fill='#172b42');d.text((22,16),f'{case.upper()} / V{j:02} / SYNTHETIC SCHEMATIC',font=font(26),fill='white')
            if j==1:
                for rect,name in [((30,130,320,390),'LAB'),((350,130,600,390),'EAST CORRIDOR'),((650,130,930,390),'EAST EXIT'),((30,430,600,560),'SERVICE CORRIDOR'),((650,430,930,560),'CAFETERIA')]:
                    d.rectangle(rect,outline='black',width=4);d.text((rect[0]+12,rect[1]+15),name,font=font(20),fill='black')
                d.line((320,260,650,260),fill='teal',width=8);d.line((160,390,160,430),fill='orange',width=8)
                d.text((45,490),'UNMONITORED LINK TO LAB',font=font(24),fill='black')
            else:
                time,place,coat,obj=scenes[j-2];d.text((30,98),place+'  |  CAMERA '+time,font=font(32),fill='black')
                d.rectangle((50,180,900,535),outline='#334155',width=5);d.rectangle((570,340,850,375),fill='#805d42')
                if coat!='none':
                    for x in ([300,470] if i==3 and j==4 else [320]):
                        d.ellipse((x,210,x+65,275),fill='#bcbcbc');d.rectangle((x-10,275,x+75,420),fill=coat);d.line((x,420,x-20,510),fill='black',width=14);d.line((x+65,420,x+85,510),fill='black',width=14)
                if obj in ['silver','cardboard']:
                    x=405 if coat!='none' else 650;y=330 if coat!='none' else 260
                    d.rectangle((x,y,x+120,y+80),fill='#b4bdc7' if obj=='silver' else '#aa814d',outline='black',width=4)
                    if obj=='silver':d.polygon([(x+60,y+15),(x+40,y+60),(x+80,y+60)],fill='black')
                if j==10:d.text((90,235),'CLOCK OFFSET +5 MINUTES' if i==2 else 'BLIND SPOT: SERVICE CORRIDOR',font=font(34),fill='black')
            image.save(public/'images'/f'V{j:02}.png')
        identity='\n'.join(f'{name}: {color} work coat.' for name,color in zip(SUSPECTS,COLORS))
        (public/'case_brief.md').write_text(f'# {case}: Missing laboratory prototype\n\nFictional investigation. Prototype last confirmed at 18:00 and discovered missing at 18:18. All images are original synthetic schematic exhibits, not photographs.\n\nFive staff identities:\n{identity}\n\nUse exhibit IDs V01–V10 and D01–D03. Coat colour is evidence of appearance, not biometric identity.\n',encoding='utf-8')
        records='18:10,Nora Vale,EAST_CORRIDOR,ENTRY\n18:12,Theo Park,CAFETERIA,ENTRY\n18:13,Ada Finch,RECEPTION,ENTRY\n'
        records+=('18:14,Nora Vale,EAST_EXIT,EXIT\n' if i==1 else '18:14,Eli Stone,SERVICE_DOOR,ENTRY\n' if i==2 else '18:14,Eli Stone,SERVICE_DOOR,ENTRY\n18:14,Maya Reed,SERVICE_DOOR,ENTRY\n')
        (public/'documents'/'D01_access.csv').write_text('time,name,door,direction\n'+records,encoding='utf-8')
        (public/'documents'/'D02_witnesses.md').write_text('# Witness statements (unverified)\nNora: I only visited the east corridor and left.\nEli: I did not approach the lab after 18:00.\nMaya: I carried a cardboard supply box at 18:11.\nTheo: I remained in the cafeteria from 18:12.\nAda: I staffed reception.\n',encoding='utf-8')
        (public/'documents'/'D03_messages.md').write_text('# Internal messages\n17:00 Eli: My project needs that prototype tomorrow.\n17:10 Maya: Please move the cardboard consumables box to the loading bay.\n17:20 Security: Coat descriptions are from shift assignments; doors log badge credentials, not biometric identity. '+('Service camera has a +5 minute clock offset.' if i==2 else 'Service corridor is a camera blind spot.')+'\n',encoding='utf-8')
        write_json(ROOT/'evaluation_private'/'ground_truth'/(case+'_evidence_map.json'),truth['visual_facts'])
    write_json(ROOT/'evaluation_private'/'ground_truth'/'detective_validation.json',{'valid':True,'cases':3,'visual_exhibits_per_case':10,'suspects_per_case':5,'ambiguous_cases':['case_03'],'ground_truth_predeclared':True})
    return truths
