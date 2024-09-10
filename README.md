# gptman

`gptman` is a Python package designed to streamline the management of OpenAI ChatGPT Assistant API prompts using local Markdown files. With gptman, developers can easily update assistant configurations and manage prompts through simple command-line interface (CLI) commands.

## Features

- **Manage Prompts**: Organize and update ChatGPT prompts stored in Markdown files.
- **Easy Configuration**: Configure OpenAI API parameters using a TOML file.
- **Simple Commands**: Push updates to multiple or single prompts effortlessly.

## Installation (TBD)

To get started with gptman, you need to install it via pip:

```bash
pip install gptman
```

## Getting Started

1. **Create an Empty Directory**: Start by creating a new directory for your project. 

2. **Create a Configuration File**: Inside this directory, create a `gptman.toml` file to store your OpenAI API key.

   ```toml
   [openai]
   api_key=<openai-api-key>
   ```

3. **Create Prompt Files**: Write your prompts in Markdown format. For example, create a file named `prompt1.md`:

   ```markdown
   ---
   id: assist_id_1234
   name: very-nice-assistant
   model: gpt-4o-mini
   ---
   This is a prompt.
   ```

4. **Directory Structure**: Ensure your directory follows this structure:

   ```
   /project-directory
   ├── gptman.toml
   ├── prompt1.md
   ```

## Usage

To upload your prompts to the OpenAI Assistant API, use the following command:

```bash
$ gptman assistant push
```

This command will look up all Markdown files in the current directory and update them accordingly.

### Example Output

```plaintext
update prompt1.md --> very-nice-assistant (assist_id_1234)
```

#### Updating Specific Prompt Files

If you wish to update a specific Markdown file, you can specify the filename as follows:

```bash
$ gptman assistant push prompt1.md
```

## Contributing

If you'd like to contribute to gptman, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the OpenAI team for providing the ChatGPT API, which makes this package possible.
```

Feel free to modify any section or ask for additional content!
