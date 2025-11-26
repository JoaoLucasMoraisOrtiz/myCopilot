# app.py
import onnxruntime_genai as og
import argparse

def main(args):
    print("Loading model...")
    model = og.Model(f'{args.model}')
    print("Model loaded")
    tokenizer = og.Tokenizer(model)
    tokenizer_stream = tokenizer.create_stream()
    search_options = {
        'max_length': 4096
    }

    chat_template = '<|user|>\n{input} <|end|>\n<|assistant|>'

    # Keep asking for input prompts in a loop
    while True:
        text = input("Input: ")
    
        # If there is a chat template, use it
        prompt = f'{chat_template.format(input=text)}'

        input_tokens = tokenizer.encode(prompt)

        params = og.GeneratorParams(model)
        params.set_search_options(**search_options)
        
        generator = og.Generator(model, params)
        generator.append_tokens(input_tokens)
        print("\nOutput: ", end='', flush=True)
        while not generator.is_done():
            generator.generate_next_token()
            new_token = generator.get_next_tokens()[0]
            print(tokenizer_stream.decode(new_token), end='', flush=True)
              
        print()
        print()

        # Delete the generator to free the captured graph for the next generator, if graph capture is enabled
        del generator


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model', type=str, required=True, help='Onnx model folder path (must contain config.json and model.onnx)')
    args = parser.parse_args()
    main(args)

