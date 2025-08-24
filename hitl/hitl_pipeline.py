import os
import difflib
from datetime import datetime


def get_text(prompt,multiline=False):
    if multiline:
        print(prompt)
        lines = []
        try:
            while True:
                line = input()
                if line == "//":
                    break
                lines.append(line)
        except KeyboardInterrupt:
            return None
        return "\n".join(lines)
    return input(prompt)


def show_diff(old, new):
    if old==new:
        return
    diff = difflib.unified_diff(old.split('\n'),new.split('\n'), 
                               fromfile='before',tofile='after',lineterm='')
    for line in diff:
        if line.startswith('+') and not line.startswith('+++'):
            print(f"\033[92m{line}\033[0m") 
        elif line.startswith('-') and not line.startswith('---'):
            print(f"\033[91m{line}\033[0m")  
        elif line.startswith('@@'):
            print(f"\033[94m{line}\033[0m")  

def edit_session(text,role):
    preview_len = min(600,len(text))
    print(f"\n{role} | {len(text)} chars | preview:{text[:preview_len]}...")
    
    choice = get_text(f"{role.lower()}: [k]eep /[e]dit / [q]uit? ")
    
    if choice == 'q':
        return None, {}
    if choice == 'k':
        return text, {'kept':True}
    
    edited = get_text("paste your version (end with '//'):",multiline=True)
    if edited is None:
        return text, {'cancelled':True}
    
    show_diff(text, edited)
    why = get_text("why? ")
    rating=None
    while rating is None:
        try:
            rating =int(get_text("rate 1-10: "))
            if not 1<=rating<= 10:
                rating=None
        except:
            pass
    return edited, {'edited':True,'why':why,'rating':rating}


def run_pipeline():
    chain = [("data/reviewed.txt", "data/writer.txt", "Writer"),
        ("data/writer.txt", "data/reviewer.txt", "Reviewer"), 
        ("data/reviewer.txt", "data/final.txt", "Editor")]

    log = []
    for input_file, output_file, role in chain:
        if not os.path.exists(input_file):
            print(f"missing: {input_file}")
            break
        with open(input_file) as f:
            text = f.read()
        
        result,meta = edit_session(text, role)
        if result is None:
            break
        with open(output_file, 'w') as f:
            f.write(result)
        log.append({
            'role': role,
            'time': datetime.now().strftime('%H:%M'),
            **meta
        })
    ratings = [entry.get('rating') for entry in log if entry.get('rating')]
    if ratings:
        print(f"\navg rating:{sum(ratings)/len(ratings):.1f}")
    edits = sum(1 for entry in log if entry.get('edited'))
    print(f"made {edits} edits across {len(log)} stages")


if __name__ =="__main__":
    run_pipeline()