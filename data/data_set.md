---
TODO: "Add YAML tags here. Delete these instructions and copy-paste the YAML tags obtained with the online tagging app: https://huggingface.co/spaces/huggingface/datasets-tagging"
---

# Dataset Card for Assetto Corsa Gym

## Table of Contents
- [Table of Contents](#table-of-contents)
- [Dataset Description](#dataset-description)
  - [Dataset Summary](#dataset-summary)
  - [Supported Tasks and Leaderboards](#supported-tasks-and-leaderboards)
  - [Languages](#languages)
- [Dataset Structure](#dataset-structure)
  - [Data Instances](#data-instances)
  - [Data Fields](#data-fields)
  - [Data Splits](#data-splits)
- [Dataset Creation](#dataset-creation)
  - [Curation Rationale](#curation-rationale)
  - [Source Data](#source-data)
  - [Annotations](#annotations)
  - [Personal and Sensitive Information](#personal-and-sensitive-information)
- [Considerations for Using the Data](#considerations-for-using-the-data)
  - [Social Impact of Dataset](#social-impact-of-dataset)
  - [Discussion of Biases](#discussion-of-biases)
  - [Other Known Limitations](#other-known-limitations)
- [Additional Information](#additional-information)
  - [Dataset Curators](#dataset-curators)
  - [Licensing Information](#licensing-information)
  - [Citation Information](#citation-information)
  - [Contributions](#contributions)

## Dataset Description

- **Homepage:**  https://dasgringuen.github.io/assetto_corsa_gym/
- **Repository:**  https://github.com/dasGringuen/assetto_corsa_gym
- **Paper:** 
- **Leaderboard:** 
- **Point of Contact:** adrianremonda@gmail.com

### Dataset Summary

64M-step dataset with 2.3M steps from human drivers and the remaining steps from Soft Actor-Critic (SAC) policies. Data was collected at UC San Diego and Graz University of Technology, involving 15 drivers completing at least five laps per track and car. Participants included a professional e-sports driver, four experts, five casual drivers, and five beginners.

### Supported Tasks and Leaderboards

Three cars and 4 tracks. Dataset from humans and form policies

### Languages

English

## Dataset Structure

See https://github.com/dasGringuen/assetto_corsa_gym/blob/main/data/paths.yml and https://github.com/dasGringuen/assetto_corsa_gym/blob/main/data/README.md

```
<track>
  <car>
    <human / policy>
      laps
```

<!-- 
### Data Instances

[More Information Needed] -->

### Data Fields

Each data field is ld file (Motec file) and a piclkke file wihc cointains the telemetry of the vehicle at 50hz

### Data Splits

[More Information Needed]

## Dataset Creation

### Curation Rationale

[More Information Needed]

### Source Data

#### Initial Data Collection and Normalization

[More Information Needed]

#### Who are the source language producers?

[More Information Needed]

### Annotations

#### Annotation process

[More Information Needed]

#### Who are the annotators?

[More Information Needed]

### Personal and Sensitive Information

[More Information Needed]

## Considerations for Using the Data

### Social Impact of Dataset

[More Information Needed]

### Discussion of Biases

[More Information Needed]

### Other Known Limitations

[More Information Needed]

## Additional Information

### Dataset Curators

[More Information Needed]

### Licensing Information

[More Information Needed]

### Citation Information

[More Information Needed]

### Contributions

Thanks to [@github-username](https://github.com/<github-username>) for adding this dataset.