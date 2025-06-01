import logging
import json

from .state import InterviewSingleton


async def main_async(configs: dict):
    interview = InterviewSingleton(configs)
    print("Provide unique identifier")
    user_id = input("User ID: ")
    session_id = user_id
    session = await interview.create_session(user_id, session_id)
    
    try:
        while True:
            response_file = input("Response text file: ")
            if not response_file:
                print("No response file provided. Exiting.")
                break
            
            response = open(response_file, "r").read().strip()
            content = await interview.proceed(user_id, session_id, response)
            if content:
                print(f"Response from agent:\n{content.parts[0].text}")
            else:
                print("No response from agent.")

            state = await interview.get_state(user_id, session_id)
            logging.info(
                "Post process session state: %s", 
                json.dumps(state, indent=2)
            )

            # await interview.reset_session(user_id, session_id)
            

    except KeyboardInterrupt:
        print("\nEnding exchange.")

