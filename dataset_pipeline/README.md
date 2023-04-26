# Dataset Pipeline

This folder contains the code to extract data from Pushshift/Reddit and clean/convert it.

Detailed description can be found in the base repo's README.

### Step 0:
Download the files from https://files.pushshift.io/reddit/submissions/
Right now this process is done manually.  May automate it in the future.

### Step 1:
Decompress and scan through the submission files looking for questions.

### Step 2:
Clean the files of markdown and unwanted values.

### Step 3:
Score files and add vectors.

## Step 4:
Upload to vector database