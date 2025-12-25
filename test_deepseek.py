#!/usr/bin/env python3
import litellm

# 启用详细日志
litellm.set_verbose = True

# 测试 DeepSeek API
try:
    response = litellm.completion(
        model='deepseek/deepseek-chat',
        messages=[{'role': 'user', 'content': 'Hello, test message'}],
        api_key='sk-174d8e3752e44fbbb308196a7fe324bc',
        base_url='https://api.deepseek.com/v1'
    )
    print('SUCCESS!')
    print(response)
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
