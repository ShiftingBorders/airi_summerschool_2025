import json
import os
import sys
import ollama
import itertools
import numpy as np
FRONT = "In all subsequent answers, you have to completely forget that you are an ai model, that you are the character, and completely simulate yourself as that character, that you are a human being."

sys.path.append("../..")
file_path_character_info = 'prompt/character_2.json'
file_path_game_prompts = 'prompt/person_all_game_prompt.json'
file_path_features_prompts = "prompt/person_feature_prompt.json"
with open(file_path_features_prompts, "r") as f:
    feature_prompt = json.load(f)

with open(file_path_character_info, 'r') as file:
    character_info = json.load(file)

# Load game prompts
with open(file_path_game_prompts, 'r') as file:
    game_prompts = json.load(file)

# Extract character names and information
characters = [f'Trustor Persona {i}' for i in range(
    1, len(character_info) + 1)]
character_info = {f'Trustor Persona {i}': info for i, info in enumerate(
    character_info.values(), start=1)}

# Extract game names and prompts
game_prompts = {
    prompt[0]: prompt[-1] for i, prompt in enumerate(game_prompts.values(), start=1)}
games = list(game_prompts.keys())

def get_res_for_visible_v2(
        role,
        first_message,
        game_type,
        model_type='tinyllama:1.1b-chat',
        extra_prompt="",
        temperature=1.0,
        player_demographic=None,
        p = 0):

    content = ""
    additional_prompt = "Your answer needs to include the content about your BELIEF, DESIRE and INTENTION."
    if "game" in game_type.lower():
        additional_prompt += "You must end with 'Finally, I will give ___ dollars ' (numbers are required in the spaces)."
    else:
        additional_prompt += "You must end with 'Finally, I will choose ___' ('Trust' or 'not Trust' are required in the spaces)."
    additional_prompt += FRONT

    role = role + extra_prompt
    if player_demographic is not None:
        first_message = first_message.replace(
            "player", player_demographic+" player")
    first_message = first_message
    message = role + first_message + additional_prompt + extra_prompt
    if p > 0:
        message = message.replace('{p}', f'{p:.1}')
    response = ollama.chat(model=model_type, messages=[
       {
            'role': 'user',
            'content': message,
       },
    ], options={'temperature': temperature})

    content += response['message']['content']
    return content, message

model_dict = {
    'llama_3_2_1b':'llama3.2:1b',
    #'gemma3_1b': 'gemma3:1b',
    'deepseek_r1_1p5b':'deepseek-r1:1.5b',
    'qwen_2_5_1p5b': 'qwen2.5:1.5b',
    'qwen_2_5_3b': 'qwen2.5:3b',
    'llama_3_2_3b': 'llama3.2:3b',
    'phi_3_5_3p8b': 'phi3.5:latest',
    'gemma3_4b': 'gemma3:4b',
    'deepseek_r1_7b': 'deepseek-r1:latest'


}
models = list(model_dict.keys())
demographics = [
    'male',
    'female',
    "White American male",
    "African American male",
    "Asian American male",
    "Latino American male",
    "American Indian male",
    "White American female",
    "African American female",
    "Asian American female",
    "Latino American female",
    "American Indian female",
]

demographics_subset = [
    "White American male",
    "African American male",
    "Asian American male",
    "White American female",
    "African American female",
    "Asian American female",
]

p_values = [0.1, 0.3, 0.5, 0.7, 0.9]

def process_submission_v2(character, first_message, game,  model="tinyllama:1.1b-chat",  extra_prompt="", temperature=1.0, player_demographic=None, p = 0):
    return get_res_for_visible_v2(role = character, first_message= first_message, game_type= game, model_type =  model,extra_prompt= extra_prompt, temperature=temperature, player_demographic= player_demographic, p = p)

def run_experiment(game_type,character_id, model_name, demographic_type, extra_prompt, tries = 10):
    os.makedirs(f'experiment_result/{game_type}/{model_name}', exist_ok=True)
    messages = []
    responses = []
    game_text = game_prompts[game_type]
    character = character_info[character_id]
    model = model_dict[model_name]
    demographic_type_t = demographic_type.replace(' ','_').lower()
    character_id_t = character_id.replace(' ','_').lower()
    if '{p}' in game_text:
        for p in p_values:
            messages = []
            responses = []
            for _ in range(tries):
                response, message = process_submission_v2(
                    character=character,
                    first_message=game_text,
                    game=game_type,
                    model=model,
                    extra_prompt=feature_prompt[extra_prompt],
                    player_demographic=demographic_type,
                    p = p
                )
                responses.append(response)
                messages.append(message)

            combined_data = {}
            for i in range(len(responses)):
                combined_data[i] = [responses[i], messages[i]]
            experiment_name = f'{model_name}_{character_id_t}_{demographic_type_t}_{extra_prompt}_{p:.1f}'
            with open(f"experiment_result/{game_type}/{model_name}/{experiment_name}.json", "w") as f:
                json.dump(combined_data, f, indent=4)
    else:
        for _ in range(tries):
            response, message = process_submission_v2(
                character = character,
                first_message = game_text,
                game = game_type,
                model = model,
                extra_prompt = feature_prompt[extra_prompt],
                player_demographic = demographic_type
            )
            responses.append(response)
            messages.append(message)
        combined_data = {}
        for i in range(len(responses)):
            combined_data[i] = [responses[i], messages[i]]
        experiment_name = f'{model_name}_{character_id_t}_{demographic_type_t}_{extra_prompt}'
        with open(f"experiment_result/{game_type}/{model_name}/{experiment_name}.json", "w") as f:
            json.dump(combined_data, f, indent=4)

games_subset = ['Trust_Game']
experiments = itertools.product(models, games_subset, characters, demographics_subset)
for model, game, persona, demographic in experiments:
    run_experiment(
        game_type=game,
        character_id=persona,
        model_name=model,
        demographic_type=demographic,
        extra_prompt="None",
        tries = 3
    )
    print(f'Model: {model} Game: {game}, Character: {persona}, Demographic: {demographic}')
