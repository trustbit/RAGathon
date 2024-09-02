def get_run_cost(run):
    usage_data = run.usage
    if usage_data:
        # prompt_tokens = usage_data.prompt_tokens
        # completion_tokens = usage_data.completion_tokens
        total_tokens = usage_data.total_tokens
        cost_per_token_input = 5 / 1000000 # USD
        cost_per_token_output = 15 / 1000000 # USD
        input_cost = usage_data.prompt_tokens * cost_per_token_input
        output_cost = usage_data.completion_tokens * cost_per_token_output   
        total_cost = input_cost + output_cost
        return total_tokens, total_cost