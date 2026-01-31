class Skill:
    name = 'base skill'
    description = 'This is the base skill.'
    api_keys_required = []

    def __init__(self, api_keys):
        self.api_keys = api_keys
        missing_keys = self.check_required_keys(api_keys)
        if missing_keys:
            print(f"Missing API keys for {self.name}: {missing_keys}")
            self.valid = False
        else:
            self.valid = True
        for key in self.api_keys_required:
            if isinstance(key, list):
                for subkey in key:
                    if subkey in api_keys:
                        setattr(self, f"{subkey}_api_key", api_keys.get(subkey))
            elif key in api_keys:
                setattr(self, f"{key}_api_key", api_keys.get(key))

    def check_required_keys(self, api_keys):
        missing_keys = []
        for key in self.api_keys_required:
            if isinstance(key, list):  # If the key is actually a list of alternatives
                if not any(k in api_keys for k in key):  # If none of the alternatives are present
                    missing_keys.append(key)  # Add the list of alternatives to the missing keys
            elif key not in api_keys:  # If the key is a single key and it's not present
                missing_keys.append(key)  # Add the key to the missing keys
        return missing_keys

    def execute(self, params, dependent_task_outputs, objective):
        raise NotImplementedError('Execute method must be implemented in subclass.')