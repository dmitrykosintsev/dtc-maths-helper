#!/bin/bash

# This script is used to install Maths Helper bot. Each operation can be performed manually
# Step 1: Rename .env.template to .env if it exists
if [ -f ".env.template" ]; then
    mv .env.template .env
    echo ".env.template renamed to .env"
else
    echo ".env.template does not exist!"
    exit 1
fi

# Step 2: Build Docker Compose images without starting them
docker-compose -f docker-compose.yaml build
if [ $? -ne 0 ]; then
    echo "Docker Compose build failed!"
    exit 1
else
    echo "Docker Compose images built successfully!"
fi

# Step 3: Download models from Huggingface and create Modelfiles
# You can download only one model. In this case, comment the models you do not need
declare -A model_files
# Each model points to an array of file URLs for that model
model_files["deepseek-math-7b-rl"]=(
    "https://huggingface.co/deepseek-ai/deepseek-math-7b-rl/blob/main/model-00001-of-000002.safetensors"
    "https://huggingface.co/deepseek-ai/deepseek-math-7b-rl/blob/main/model-00002-of-000002.safetensors"
)
model_files["Qwen2-Math-7B-Instruct"]=(
    "https://huggingface.co/Qwen/Qwen2-Math-7B-Instruct/blob/main/model-00001-of-00004.safetensors"
    "https://huggingface.co/Qwen/Qwen2-Math-7B-Instruct/blob/main/model-00002-of-00004.safetensors"
    "https://huggingface.co/Qwen/Qwen2-Math-7B-Instruct/blob/main/model-00003-of-00004.safetensors"
    "https://huggingface.co/Qwen/Qwen2-Math-7B-Instruct/blob/main/model-00004-of-00004.safetensors"
)
model_files["MathCoder-CL-7B"]=(
    "https://huggingface.co/MathLLMs/MathCoder-CL-7B/blob/main/model-00001-of-00002.safetensors"
    "https://huggingface.co/MathLLMs/MathCoder-CL-7B/blob/main/model-00002-of-00002.safetensors"
)

for model in "${!model_files[@]}"; do
    model_dir="./ollama/models/$model"
    mkdir -p "$model_dir"

    echo "Downloading files for $model..."
    modelfile_content=""

    # Loop through each safetensor file for the current model
    for file_url in "${model_files[$model][@]}"; do
        file_name=$(basename "$file_url")  # Extract file name from URL
        curl -L "$file_url" -o "$model_dir/$file_name"
        if [ $? -ne 0 ]; then
            echo "Failed to download $file_name from $file_url!"
            exit 1
        else
            echo "$file_name downloaded successfully!"
        fi
        # Add safetensor file path to Modelfile content
        modelfile_content+="$model_dir/$file_name"$'\n'
    done

    # Write all safetensor paths to the Modelfile
    echo "$modelfile_content" > "$model_dir/Modelfile"
    echo "Modelfile created for $model"
done

# Step 4: Start Docker Compose services in detached mode
docker-compose -f docker-compose.yaml up -d
if [ $? -ne 0 ]; then
    echo "Failed to start Docker Compose services!"
    exit 1
else
    echo "Docker Compose services started successfully!"
fi

# Step 5: Run 'ollama create' inside the Ollama container
ollama_container=$(docker-compose ps -q ollama)  # Get the Ollama container ID
if [ -z "$ollama_container" ]; then
    echo "Ollama container is not running!"
    exit 1
fi

# Import downloaded models into Ollama
for model in "${!model_files[@]}"; do
    docker exec "$ollama_container" ollama create "$model"
    if [ $? -ne 0 ]; then
        echo "Failed to import $model into Ollama!"
        exit 1
    else
        echo "$model imported into Ollama successfully!"
    fi
done

# Step 6: Display the list of imported models
echo "Displaying the list of imported models:"
docker exec "$ollama_container" ollama list

# Step 7: Bring down Docker Compose services
docker-compose down
if [ $? -ne 0 ]; then
    echo "Failed to bring down Docker Compose services!"
    exit 1
else
    echo "Docker Compose services brought down successfully!"
fi

echo "Successfully installed!"
