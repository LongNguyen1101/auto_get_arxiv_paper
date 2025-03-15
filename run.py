from config import get_config
from func import main

config = get_config()

if __name__ == "__main__":
    main(config['url'], config['search_query'], 
         config['sortBy'], config['sortOrder'], config['max_results'])
