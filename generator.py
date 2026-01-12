import json
import os

def load_exercises():
    try:
        with open('exercises.json', 'r', encoding='utf-8') as file:
            content = file.read().strip()
            if not content:
                print("Error: exercises.json is empty.")
                return []
            data = json.loads(content)
            return data['exercises']
    except json.JSONDecodeError as e:
        print(f"JSON Syntax Error: {e}")
        return []
    except FileNotFoundError:
        print("Error: exercises.json not found in this folder.")
        return []

def generate_workout(available_mins, crowd_pct, target_muscle="All"):
    exercises = load_exercises()
    if not exercises:
        return [], 0

    if target_muscle.lower() != "all":
        targets = {t.strip().lower() for t in target_muscle.split(",")}
        filtered = []
        for ex in exercises:
            m_group = (ex.get('muscle_group') or "").lower()
            if m_group in targets:
                filtered.append(ex)
        exercises = filtered

    available_secs = available_mins * 60
    exercises.sort(key=lambda x: x.get('is_compound', False), reverse=True)

    workout_plan = []
    current_time_secs = 0  
    wait_per_set = (crowd_pct / 100) * 30 

    for ex in exercises:
        sets = 3
        reps = "6-10" if ex.get('is_compound') else "12-15"
        
        set_dur = ex.get('set duration', 60) 
        rest_dur = ex.get('recommended rest duration', 90)
        
        total_ex_time = (sets * set_dur) + ((sets - 1) * rest_dur) + (sets * wait_per_set)

        if current_time_secs + total_ex_time <= available_secs:
            workout_plan.append({
                "name": ex['name'],
                "muscle": ex.get('muscle_group'),
                "sets": sets,
                "reps": reps,
                "duration": round(total_ex_time / 60, 1),
                "rest": ex.get('recommended rest duration', 90) # Add this line
            })
            current_time_secs += total_ex_time

    return workout_plan, current_time_secs

if __name__ == "__main__":
    try:
        print("\n--- Welcome to the PF Workout Architect ---")
        user_mins = int(input("How many minutes do you have? "))
        user_crowd = int(input("How crowded is the gym (0-100%)? "))
        
        print("\nMuscle Groups: Chest, Back, Legs, Arms, Shoulders, Core, Glutes, or All")
        user_muscle = input("What do you want to train? ").strip() or "All"
        
        plan, total_time = generate_workout(user_mins, user_crowd, user_muscle)

        if plan:
            print(f"\n{'='*45}")
            print(f"--- YOUR {user_mins} MINUTE {user_muscle.upper()} ROUTINE ---")
            print(f"{'='*45}")
            
            for i, item in enumerate(plan, 1):
                print(f"{i}. {item['name']} ({item['muscle']})")
                print(f"   Targets: {item['sets']} sets x {item['reps']} reps")
                print(f"   Allocated Time: {item['duration']} minutes")
                print("-" * 25)
                
            print(f"TOTAL ESTIMATED GYM TIME: {round(total_time / 60, 1)} minutes")
            print(f"{'='*45}\n")
        else:
            print(f"\nNo {user_muscle} exercises fit in that time frame. Try more time!")

    except ValueError:
        print("Error: Please enter numbers only for time and crowdedness.")