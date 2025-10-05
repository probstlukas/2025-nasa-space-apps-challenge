# 🔭 2025 NASA Space Apps Challenge

## Usage
```bash
docker build -t nasa-space-apps .
docker run -p 8080:8080 nasa-space-apps
```


## Challenge Description

### Summary

Enable a new era of human space exploration! NASA has been performing biology experiments in space for decades, generating a tremendous amount of information that will need to be considered as humans prepare to revisit the Moon and explore Mars. Although this knowledge is publicly available, it can be difficult for potential users to find information that pertains to their specific interests. Your challenge is to build a dynamic dashboard that leverages artificial intelligence (AI), knowledge graphs, and/or other tools to summarize a set of NASA bioscience publications and enables users to explore the impacts and results of the experiments these publications describe.

### Background
Exploring the Moon and Mars safely and efficiently requires an understanding of how humans, plants, and other living systems respond to the space environment. The NASA Biological and Physical Sciences Division funds research targeted towards addressing the high-priority science required to enable future human exploration efforts. These in-space experiments have resulted in numerous scientific breakthroughs that have informed mission planning and technology development. A list of publications describing these experiments exists; however, it can be challenging for potential users to comprehend the trove of results obtained from the diverse experiments performed over many years. Emerging approaches in informatics and AI offer an opportunity to rethink how this information can be better organized and summarized to describe research progress, identify gaps where additional research is needed, and provide actionable information.

### Objectives
Your challenge is to build a functional web application that leverages AI, knowledge graphs, and/or other tools to summarize the 608 NASA bioscience publications listed in an online repository (see Resources tab), and enables users to explore the impacts and results from the experiments those publications describe.

Your tool could take the form of a dynamic dashboard that allows interactive search and interrogation of this collection of studies. Think about the functionalities that would be most impactful to users and how your tool could incorporate them. For example, your tool could help identify areas of scientific progress, knowledge gaps, areas of consensus or disagreement, or provide actionable insights to mission planners.

### Potential Considerations
You may (but are not required to) consider the following:

* Your target audience could include:
  * Scientists who are generating new hypotheses
  * Managers identifying opportunities for investment
  * Mission architects looking to explore the Moon and Mars safely and efficiently
* If you choose to use tools that mine the text of publications, think about which sections of text (e.g., Introduction, Results, Conclusion) may provide the most relevant content for a given purpose. For example, the Results sections may provide objectively demonstrated information, while the Conclusion sections may be more forward-looking.
* Feel free to use non-traditional approaches for searching and summarizing research results, including visual, audio, or other representations.
* Your tool could also leverage other NASA resources to provide additional context regarding these studies (see Resources tab):
  * The NASA Open Science Data Repository (OSDR) contains the primary data and metadata from many of these studies.
  * The NASA Space Life Sciences Library contains additional relevant publications.
  * The NASA Task Book contains information on the grants that funded some of these studies.

### NASA Data & Resources

* [A list of 608 full-text open-access Space Biology publications](https://github.com/jgalazka/SB_publications/tree/main): This resource provides links to access 608 full-text space biology publications. Open the .csv file to see titles

* [NASA Open Science Data Repository](https://www.nasa.gov/osdr/): The NASA Open Science Data Repository (OSDR) provides access to data from over 500 biological experiments either performed in space, or in support of space exploration.

* [NASA Space Life Sciences Library](https://public.ksc.nasa.gov/nslsl/): The NASA Space Life Sciences Library (NSLSL) consolidates global space life sciences literature into a single database to support research that addresses the effects of the space environment on biological systems.

* [NASA Task Book](https://taskbook.nasaprs.com/tbp/welcome.cfm): The NASA Task Book is an online database of research projects supported by NASA's Biological and Physical Sciences (BPS) Division and Human Research Program (HRP). Users can view project descriptions, annual progress, final reports, and bibliographical listings of publications resulting from NASA-funded studies in Space Biology, Physical Sciences, and Human Research. Visitors can also learn about the potential impact of these studies and the anticipated benefits that such research could offer to us on Earth.
