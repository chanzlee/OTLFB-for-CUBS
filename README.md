# Online Timeline Follow Back Survey
O-TLFB by CUChange

## Info
### Background

The Online Timeline Followback (O-TLFB) is a novel, web-based administration tool for Sobel and Sobel’s Timeline
Followback retrospective substance use assessment (Sobel, 1992). The O-TLFB was developed by the Center for Health and
Neuroscience, Genes and Environment (CUChange) at the University of Colorado Boulder in collaboration with Trailblazing
Technology (@zachmccormick). The development, implementation, and layout of the O-TLFB are documented in detail in the
Journal for Biomedical Informatics (JBI) (Martin-Willett et al, 2019) and the validation study of the tool is documented
in Brain and Behavior (Martin-Willett et al, 2019).

As described in the JBI paper, the CUChange development team intended the use of the O-TLFB to be free and open source
to all research groups. The O-TLFB can be hosted on Heroku using the provided Procfile or locally by following the
Running Locally guide. When running locally the O-TLFB is capable of running offline, however you will have to manually
upload the data from the admin page when you are back online. Broadly, it consists of three components; a web-based user
interface, a Heroku-based data collection and management system, and a REDCap-based data storage and summary project
(Harris et al, 2009).

The CUChange development team is not responsible for the implementation of the O-TLFB for any groups who make use of the
materials contained in this repository.  Groups are responsible for the modification and implementation of all aspects
of the O-TLFB, including access to resources such as REDCap. All instructions provided below are for OSX; additional
support will not be provided for other operating systems. No group-specific support will be provided by CUChange unless
otherwise arranged. All research or other groups who make use of the O-TLFB should cite the CUChange development team in
any publications, presentations or manuscripts. Complete APA citations are provided below:

Martin-Willett R, Helmuth T, Bryan AD, Abraha M, Lee K, Hitchcock LN, Bidwell LC. (2019) Validation of a multi-substance
online timeline follow-back assessment. Brain and Behavior.

Martin-Willett R, McCormick Z, Newman W, Torres Ortiz M, Larsen L, Bidwell LC. (2019) The transformation of a gold
standard in-person substance use assessment to a web-based, REDCap integrated data capture tool. Journal of Biomedical
Informatics, 94.

### Feedback

Your feedback as well as any suggestions for improving the code would be much appreciated. If you are familiar with git.
You may use the survey linked below to submit feedback or fork the code and create a pull request on a new branch
for our review.


[REDCap Project](https://redcap.ucdenver.edu/surveys/?s=T8YYRTDX9P)

---

## System Requirements
We strongly recommend using Heroku to host your TLFB, but if you want to host it on your own you'll need to setup an environment similar to Heroku. We can not assist you with this process, but you can reference [Heroku's documentation](https://devcenter.heroku.com/categories/working-with-django) for more information. But for a general idea:

- Processors: You need 2 processors with 512MB of RAM each ([more info](https://devcenter.heroku.com/articles/dyno-types))
  - One processor for the Django web application itself
  - One processor for the data transformation process to upload to REDCap
- Storage: 
  - 10GB of storage for the PostgreSQL database
  - 20MB folder for the code itself
  - 500MB for python libraries
- Operating System:
  - We run on the [Heroku-18 Stack](https://devcenter.heroku.com/articles/heroku-18-stack), which runs on Ubuntu 18.04

For more information, please reference the [Heroku developer center](https://devcenter.heroku.com/). We can not assist in setting up these environments, but Heroku was the best solution for our team and we strongly reccomend it.

---

## Setup for Running on Heroku
You will need to have both a github and a heroku account that are linked to each other to make this processes easier.

### Step 1: Clone GitHub Project
In [GitHub](http://github.com) you will need to create a new repository for your version of the O-TLFB. When you create the new repository, you
will choose the option `Import Code` to use an existing repo. You can then use the URL for this project
`https://github.com/cuchange/O-TLFB` and click **Begin Import**. GitHub will do all the work of setting it up, and you
will be good to modify the code as you wish.

### Step 2: Heroku Project Creation
In [Heroku](http://heroku.com) you will need to create a Heroku project to host your O-TLFB. This will be easy if you have
your github account linked to your Heroku. With your heroku project opened, you can go to the **_Deploy_** page in the
page options at the top. In the _**Deploy**_ page, you should see a button that says **GitHub**`Connect to GitHub` click
that, and you should see a new section that says _"Search for a repository to connect to"_, here is where you can enter
your repository name. Click enter to search, and you will click the `Connect` button next to your repository name.

After, to make things easier, you should click the `Enable Automatic Deploys` option when it shows up. This will
allow the code to automatically update whenever you make changes to the main branch. Just remember that you should
only commit changes to the main branch if you know everything is working well. Since it is your first time running the
app, you will need to `Deploy Branch` in the _Manual deploy_ section. This will get all the code loaded onto heroku.

Finally, see the working O-TLFB you can go to **_Settings_** in the page options and scroll down until you see
_Domains_. You should see a URL similar to `https://heroku-project-name.herokuapp.com/` and that will be where your
O-TLFB is hosted.

Note: We use two dyno's to also run the section of code that exports data to REDCap, in order to activate that you will
need to pay for a second dyno. This will also require that you delete the TODO section from the
`tlfb/transform_helper.py` and add the following to the **Config Vars** by selecting `Reveal Config Vars` and adding:

| KEY | VALUE |
| --- | ----- |
| API_URL | `'https://redcap.ucdenver.edu/api/'` |
| COHORT_KEY_TABLE_TOKEN | `'[ SURVEY API TOKEN WITH PHONE AND FIRST LETTER ]'` |
| TLFB_TOKEN | `'[ TLFB API TOKEN ]'` |

### Step 3: Create Admin User
In order to access your Admin page `https://heroku-project-name.herokuapp.com/admin` you will need to create a super
user on heroku. You can do this on the heroku website by going to `More` near the top right of your project screen
and selecting the _Run console_ option. A console will pop-up and you can enter the following:

```
python manage.py createsuperuser
```

It will then ask you for a username, email, and password that you will enter twice. This is the username and password
for your admin page, so do not forget it. When you login, you will have a list of options, you will select the **_Rough
datas_** option to see the saved O-TLFB data. I would check here after each session to make sure the data was stored
correctly.

---

## Setup for Running Locally


### Step 1: Setup Local Environment

Follow the instruction guide of your operating system to set up the project environment. All machines and operating 
systems are different, so you will need to trouble shoot any errors that you run into on your own. 

[Setup Instructions for OSX](./setup_instructions/OSX.md)

[Setup Instructions for Linux (Debian/Ubuntu)](./setup_instructions/LINUX.md)

[Setup Instructions for Windows](./setup_instructions/WINDOWS.md)

### Step 2: Running O-TLFB

Before you run, make sure you have completed the TODO's in the `tlfb/views.py` and the `tlfb/transform_helper.py`.
Everything will still work without this, but it will not upload data to your desired location automatically if this is
not setup.

To actually run the entire service, type `./manage.py runserver`. This will run the server
locally at `http://127.0.0.1:8000/` (or alternatively accessible at `http://localhost:8000/`. At this point you
should be able to use everything in your browser. Errors will not propagate up to Sentry. However, data will submit to
Redcap when you complete a survey.

To start the celery worker execute the following command in the project directory. Note: you will need to run this in
a separate terminal from the terminal running the django app.

```
celery -A tlfb.tasks worker --loglevel=info
```

---

## Setting up REDCap Project/Data Endpoint

### REDCap Project

If you are familiar with REDCap projects, you will know that a Project can be created using Data Dictionary of an 
existing REDCap Project. We have provided a copy of our projects data dict 
([OTLFB Data Dict.csv](./setup_instructions/OTLFB%20Data%20Dict.csv)) 
for you to use when initializing your REDCap project. After creating your project, you will want to make sure that your
PI has API import and export rights, so they can generate a project API token. This API token allows data to be 
imported directly into the REDCap project once a participant has submitted their response.

To give someone API rights, you will go to the __User Rights__ page by going to __Project Setup > User Rights and 
Permissions > User Rights.__ Once there, you can select the account you want to generate the API token and select
__Edit user privileges__, which should show a pop up window. Here you will make sure to check off the boxes that are
labeld __API Export__, __API Import/Update__, and __Create Records__. 

To get an API Token, you will go to the menu and select the Application called __API__. In this application, you will be
able click a button labeld __Request API token__ - this will take some time to process, so check back some time later.
Once you have the API token, you can update the __TLFB_TOKEN__ in the ``tlfb/transform_helper.py`` file. You will 
replace the ``[ YOUR TLFB API TOKEN ]`` inside of the single quotes with your API Token.

### Data End Point

Although this project was set up to use REDCap, you can choose to use a different endpoint. The __transform_data()__ 
function Exports the raw data into a CSV file. This CSV file can be used to send to a different Endpoint. The data 
transfer function can be found in the same file __export_transformed_data()__ which sends a request holding the CSV data 
to the REDCap API. The header of the export file is going to be the __Variable / Field Name__ in the data dictionary 
file provided: [OTLFB Data Dict.csv](./setup_instructions/OTLFB%20Data%20Dict.csv)

---

## Modifying O-TLFB
### Modifying - Login

The Login is a Django form, so all modifications can be made to the `tlfb/forms.py` file, under the LoginForm class.
PhoneWidget is used because so participants can enter in their entire number without having to worry about formatting
options. Although we ask for their full phone number, we only ask for the last five digits so there isn't any
identifying data in the database. However since that is not unique we also ask for the first letter of their first name
and pass in a cohort through the URL. This helps reduce any data collisions/mix-ups in the assignment of the ID.

### Modifying - URL Arguments

URL arguments can be passed by adding '?' to the end of the URL followed by the argument you want to add, any subsequent
argument has to have and '&' between it and the last argument. The URL should look like this:
```
https://your_unique_url.edu/?arg1=True&arg2=10&arg3=flag
```
You can add more arguments to the code in order to modify forms to show or hide specific surveys or modify what text is
shown for a specific survey. The current functionality that we have available is:

| argument    | type        | default | description |
| :--- | :----: | :----: | :--- |
| days | int | 14 | Specify how many days of TLFB are going to be collected. |
| offset | int | 0 | Specify how many days prior to today that the baseline should end. |
| with_study_cbs | bool | False | Specify weather or not to show study cannabis when cannabis is selected. |
| prescription | bool | False | Specify weather or not to collect prescription medication. |
| cohort | str | `''` | Specify what cohort the participant receiving the URL is in. |

For example, you can set up a unique url for each time point:

- T1: `/?days=30&offset=16&cohor=studynum1` 30 day TLFB, ending 16 days from today, and we know someone using this URL is
  in study 1
- T2: `/?cohor=studynum1&with_study_cbs=True` 14 day TLFB, ending today, in study 1, and we are going to be collecting
study cannabis information.

### Modifying - Survey Instructions

The instructions are defined at the marker date page after log-in. To modify this text, you will need to go to the
`tlfb/templates/step1_markerdates.html` file.

### Modifying - Surveys

To modify the survey, you need to go into the `tlfb/forms.py` file and then the `tlfb/wizards.py`
Here you see all of the form classes that are used to define the survey forms. The base classes are:
- **SubstanceDrilldownForm**
  - The base substances that are going show up when they are entering information for a specific
  date. The URL arguments can be used here to show specific substances for different timepoints or studies.
- DrilldownForm
  - Every survey with multiple options is a DrilldownForm and those options are passed as a list to the
  vairable OPTIONS. For more embedding you can pass another DrilldownForm, or you can pass
- SubstanceDetailForm
  - Every substance is a SubstanceDetailForm, for example Alcohol has an option of beer, liquor,
  wine as a substance, and each substance will have a specific label and variable name, so it can be referenced in the
  export and summary variable calculator.

Once you have created the class, you can link the class to the form in the `wizards.py` file. To add in custom survey
forms you can look at the Django forms documentation, or use any of ours as reference.

### Modifying - Summary Calculations

The current O-TLFB calculates total amount, total days, and average (amount/days). These are calculated inside of the
`tlfb/redcap_helper.py` file. The `from_json_to_redcap_json` function contains the a dictionary of all of the summary
variables and here is where add or modify the summary variables.

It is important to note that we have encodings for different types empty entries and summary calculations. Here is the
meaning of each:

| value | daily value meaning | summary value meaning |
| ----- | :----: | :--- |
| -9999 | Participant entered 'Unknown' as there response | All entered daily values were 'Unknown' |
| -8888 | Nothing was selected from the drop down option | All entered daily values had nothing selected from the drop down |
| -8989 | N/A | A mix of only 'Unknown' was selected and nothing selected responses were submitted |
