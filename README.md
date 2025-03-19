# BA-bench
Business Analytics Benchmark for GenAI Agents

## Contribution Data Format

We aim to structure each sample (question-level) in our BA-bench using the following json format:

```python
{
    'id': str,  # Unique identifier for each sample
    'question': str,  # A business-related question related to the data
    'data_file': str,  # The data file the question relates to
    'doc_file': str,  # The document file the question relates to
    'answer': str,  # The answer to the question
    'data_domain': str,  # The domain the data belongs to (e.g., finance, education)
    'analysis_type': str,  # The type of question, optional: ["Structure problems", "Unstructured problems", "Chart problems"]
    'origin_from': list[str],  # Source of the question, e.g., ['benchmark name', 'question id']
    'additional_information': list[dict[str, str]],  # Additional information such as code, statistical results, intermediate steps (e.g., StatQA's analysis methods) etc.
}
```

### Analysis Type Definitions:
- **Structure problems**: The answer is structured (e.g., numerical, categorical).  
  *Example*: A sample from *StatQA* where the `answer` is a column and analysis method. If the agent's answer matches them, it is considered correct.
  [comment]: Shall we not include such questions if the answer is not an actual answer? I'd like all the questions in the benchmark can at least have an answer.


- **Unstructured problems**: The answer is unstructured (e.g., text-based).  
  *Example*: A sample from *InsightBench* where the `answer` is an insight. Semantic similarity must be considered.
  
- **Chart problems**: The answer is a plot.  
  *Example*: A sample from *VisEval* where the answer is a plot. The agent must write code to generate it.

---

### Example Formats

#### **StatQA Format**
```python
{
    'dataset': 'Dataset for Admission in the University',
    'refined_question': 'Is the variability in GRE scores not significantly different from that in Letter of Recommendation?',
    'relevant_column': '[{"column_header": "GRE Score", "is_strata": false, "is_control": false}, {"column_header": "LOR", "is_strata": false, "is_control": false}]',
    'results': '[{"method": "Mood Variance Test", "result": "{\"stat\": 0.0, \"p value\": 1.0}", "conclusion": "Variance not significantly different between them"}, {"method": "Levene Test", "result": "{\"stat\": 735.69701, \"p value\": 0.0}", "conclusion": "Variance significantly different between them"}]',
    'answer': '{"columns": ["GRE Score", "LOR"], "methods": ["Mood Variance Test", "Levene Test"]}',
    'task': 'Variance Test',
    'difficulty': 'hard',
    'domain': 'Education & Student Performance'
}
```

#### **InfAgent-DAbench Format**
```python
{
    'id': 0,
    'question': 'Calculate the mean fare paid by the passengers.',
    'concepts': ['Summary Statistics'],
    'constraints': "Calculate the mean fare using Python's built-in statistics module or an appropriate method in pandas. Round off the answer to two decimal places.",
    'format': '@mean_fare[mean_fare_value] where "mean_fare_value" is a floating-point number rounded to two decimal places.',
    'file_name': 'test_ave.csv',
    'level': 'easy',
    'domain': 'Tourism'
}
```

#### **InsightBench Format**
```python
{
    "data_type": "descriptive",
    "insight": "The Hardware incidents are significantly higher in volume than others",
    "insight_value": {
        "x_val": "Hardware",
        "y_val": 335
    },
    "plot": {
        "plot_type": "histogram",
        "title": "Incidents by Category",
        "x_axis": {
            "name": "Category",
            "value": ["Hardware", "Software", "Network", "Inquiry / Help", "Database"],
            "description": "This represents the different categories of incidents."
        },
        "y_axis": {
            "name": "Number of Incidents",
            "value": [336, 41, 51, 32, 40],
            "description": "This represents the number of incidents in each category."
        },
        "description": "The histogram displays the distribution of incidents across different categories. Each bar represents a category, and the length of the bar corresponds to the number of incidents in that category. The 'Hardware' category has the highest number of incidents."
    },
    "question": "What is the distribution of incidents across all categories?",
    "actionable_insight": "Since the Hardware category has the highest number of incidents, it may be beneficial to allocate more resources or provide additional training to the team handling these incidents.",
    "code": "plot = df.groupby(\"category\").size().plot(kind=\"barh\", color=sns.palettes.mpl_palette(\"Dark2\"))\n\nfig = plt.gcf()\n\nfor i in plot.patches:\n    x_value = i.get_width()\n    y_value = i.get_y() + i.get_height() / 2\n    label = \"{:.1f}\".format(x_value)\n    plt.annotate(label, (x_value, y_value), xytext=(-10, 0), textcoords=\"offset points\", ha='right', va='center')\n\nplt.title('Incidents Distribution by Category')\nplt.xlabel('Category')\nplt.ylabel('Number of Incidents')\nplt.show()"
}
```


## Potentioal Benchmark

1. InsightBench
```
@article{sahu2024insightbench,
  title={Insightbench: Evaluating business analytics agents through multi-step insight generation},
  author={Sahu, Gaurav and Puri, Abhay and Rodriguez, Juan and Abaskohi, Amirhossein and Chegini, Mohammad and Drouin, Alexandre and Taslakian, Perouz and Zantedeschi, Valentina and Lacoste, Alexandre and Vazquez, David and others},
  journal={arXiv preprint arXiv:2407.06423},
  year={2024}
}
```
2. Infiagent-dabench
```
@article{hu2024infiagent,
  title={Infiagent-dabench: Evaluating agents on data analysis tasks},
  author={Hu, Xueyu and Zhao, Ziyu and Wei, Shuang and Chai, Ziwei and Ma, Qianli and Wang, Guoyin and Wang, Xuwu and Su, Jing and Xu, Jingjing and Zhu, Ming and others},
  journal={arXiv preprint arXiv:2401.05507},
  year={2024}
}
```

3. StatQA
```
@article{zhu2024large,
  title={Are Large Language Models Good Statisticians?},
  author={Zhu, Yizhang and Du, Shiyin and Li, Boyan and Luo, Yuyu and Tang, Nan},
  journal={arXiv preprint arXiv:2406.07815},
  year={2024}
}
```

4. DSBench
```
@article{jing2024dsbench,
  title={DSBench: How Far Are Data Science Agents to Becoming Data Science Experts?},
  author={Jing, Liqiang and Huang, Zhehui and Wang, Xiaoyang and Yao, Wenlin and Yu, Wenhao and Ma, Kaixin and Zhang, Hongming and Du, Xinya and Yu, Dong},
  journal={arXiv preprint arXiv:2409.07703},
  year={2024}
}
```

5. BLADE
```
@misc{guBLADEBenchmarkingLanguage2024,
  title = {BLADE: Benchmarking Language Model Agents for Data-Driven Science},
  author = {Gu, Ken and Shang, Ruoxi and Jiang, Ruien and Kuang, Keying and Lin, Richard-John and Lyu, Donghe and Mao, Yue and Pan, Youran and Wu, Teng and Yu, Jiaqian and Zhang, Yikun and Zhang, Tianmai M. and Zhu, Lanyi and Merrill, Mike A. and Heer, Jeffrey and Althoff, Tim},
  year = {2024},
  month = aug,
  number = {arXiv:2408.09667},
  eprint = {2408.09667},
  primaryclass = {cs},
  publisher = {arXiv},
  doi = {10.48550/arXiv.2408.09667}
}
```

6. VisEval
```
@article{chenVisEvalBenchmarkData2025,
  title = {{{VisEval}}: {{A Benchmark}} for {{Data Visualization}} in the {{Era}} of {{Large Language Models}}},
  author = {Chen, Nan and Zhang, Yuge and Xu, Jiahang and Ren, Kan and Yang, Yuqing},
  year = {2025},
  month = jan,
  journal = {IEEE Transactions on Visualization and Computer Graphics},
  volume = {31},
  number = {1},
  pages = {1301--1311},
  issn = {1941-0506},
  doi = {10.1109/TVCG.2024.3456320}
}

```

## Collaboration Work
* one person to process InsightBench (Yingyi)
* one person to process StatQA and Infiagent-dabench

A exapmle the data can transmit to
```python
{
    'dataset': 'Dataset for Admission in the University',
    'refined_question': 'Is the variability in GRE scores not significantly different from that in Letter of Recommendation?',
    'relevant_column': '[{"column_header": "GRE Score", "is_strata": false, "is_control": false}, {"column_header": "LOR", "is_strata": false, "is_control": false}]',
    'results': '[{"method": "Mood Variance Test", "result": "{\"stat\": 0.0, \"p value\": 1.0}", "conclusion": "Variance not significantly different between them"}, {"method": "Levene Test", "result": "{\"stat\": 735.69701, \"p value\": 0.0}", "conclusion": "Variance significantly different between them"}]',
    'answer': '{"columns": ["GRE Score", "LOR"], "methods": ["Mood Variance Test", "Levene Test"]}',
    'task': 'Variance Test',
    'difficulty': 'hard',
    'domain': 'Education & Student Performance'
}
```

[comment]: Again, let's use a different example for this one. 
```python
{
    'id': "01", 
    'question': "Is the variability in GRE scores not significantly different from that in Letter of Recommendation?",  
    'data_file':  'Dataset for Admission in the University.csv',
    'doc_file': 'None',  
    'answer': '{"columns": ["GRE Score", "LOR"], "methods": ["Mood Variance Test", "Levene Test"]}', 
    'data_domain': 'Education & Student Performance', 
    'analysis_type': 'Structure problems',  
    'origin_from': ["StatQA","refined_question"], 
    'additional_information': {
        'relevant_column': '[{"column_header": "GRE Score", "is_strata": false, "is_control": false}, {"column_header": "LOR", "is_strata": false, "is_control": false}]',
        'results': '[{"method": "Mood Variance Test", "result": "{\"stat\": 0.0, \"p value\": 1.0}", "conclusion": "Variance not significantly different between them"}, {"method": "Levene Test", "result": "{\"stat\": 735.69701, \"p value\": 0.0}", "conclusion": "Variance significantly different between them"}]',
        'task': 'Variance Test',
        'difficulty': 'hard',
    }
}
```