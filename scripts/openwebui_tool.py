import requests
from typing import Callable, Any

class Tools:
    def __init__(self):
        pass

    def search_lab_codebase(self, query: str) -> str:
        """
        Search the Olugboji lab codebase for functions, scripts, or examples.
        Use this tool whenever the user asks about lab code, existing scripts, 
        or how a specific data pipeline is implemented in the lab.
        
        :param query: A semantic description of what you are looking for (e.g., 'how to plot RF data', 'receiver function deconvolution').
        :return: A string containing the most relevant code snippets and their file paths.
        """
        try:
            # host.docker.internal is used to reach the host machine from inside the Open WebUI docker container
            # Alternatively, if running natively, use 127.0.0.1
            url = "http://host.docker.internal:8502/search"
            
            # Send the request to the FastAPI backend running on inferencelocal
            response = requests.get(url, params={"q": query}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    return f"Error searching codebase: {data['error']}"
                
                results = data.get("results", [])
                if not results:
                    return "No matching code found in the lab codebase for that query."
                
                # Format the results into a single string for the LLM to read
                formatted_results = "Here are the top matches from the lab codebase:\n\n"
                for i, doc in enumerate(results):
                    formatted_results += f"--- Match {i+1} ---\n{doc}\n\n"
                    
                return formatted_results
            else:
                return f"Failed to reach CodeSearch API. HTTP Status: {response.status_code}"
                
        except Exception as e:
            return f"An exception occurred while searching the codebase: {str(e)}"
