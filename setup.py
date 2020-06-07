from setuptools import setup, find_packages 
  
long_description = 'Helper Package made for extracting data from Nexus output file.'
  
setup( 
        name ='outStat4nex', 
        version ='1.0.0', 
        author ='Alain Dupuy', 
        author_email ='eup31000@gmail.com', 
        url ='https://github.com/eup31000/outStat4nex', 
        description ='Helper Package for simulation output well status summary export to Excel.', 
        long_description = long_description, 
        long_description_content_type ="text/markdown", 
        license ='MIT', 
        packages = ['outStat4nex'], 
        entry_points ={ 
            'console_scripts': [ 
                'outStat = outStat4nex.out_stat_4nex:entry'
            ] 
        }, 
        classifiers =[
            "Programming Language :: Python :: 3", 
            "License :: OSI Approved :: MIT License", 
            "Operating System :: OS Independent" 
        ], 
        keywords ='reservoir simulation ouput', 
        install_requires = ['pandas', 'xlsxwriter'], 
        zip_safe = False
) 