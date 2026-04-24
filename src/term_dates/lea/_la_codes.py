"""Reference data for English Local Authorities with school responsibilities.

Each entry is (name, region, term_dates_url-or-None).

Notes:
* Names follow GIAS canonical forms ("Get Information about Schools").
* Region groupings follow ONS Government Office Regions.
* DfE 3-digit LA codes are intentionally **not** embedded here — they change
  on local-government reorganisations (the 2023 unitarisations being the most
  recent example) and the authoritative list is published by GIAS at
  https://get-information-schools.service.gov.uk/Guidance/LaNameCodes
  Use term_dates.lea.codes.fetch_la_codes() to load them on demand.
* URLs are best-effort known landing pages for each authority's published
  school term dates. They get reorganised periodically — please open a PR if
  you spot a broken one.
"""

from __future__ import annotations

LA_REFERENCE: tuple[tuple[str, str, str | None], ...] = (
    # East Midlands
    ("Derby", "East Midlands", "https://www.derby.gov.uk/education-and-learning/schools-and-colleges/term-dates-and-school-holidays/"),
    ("Derbyshire", "East Midlands", "https://www.derbyshire.gov.uk/education/schools/term-dates/term-dates.aspx"),
    ("Leicester", "East Midlands", "https://www.leicester.gov.uk/schools-and-learning/school-and-college-life/school-term-and-holiday-dates/"),
    ("Leicestershire", "East Midlands", "https://www.leicestershire.gov.uk/education-and-children/schools-colleges-and-academies/term-and-holiday-dates"),
    ("Lincolnshire", "East Midlands", "https://www.lincolnshire.gov.uk/school-attendance/school-term-times"),
    ("North Northamptonshire", "East Midlands", "https://www.northnorthants.gov.uk/schools-and-education/school-term-and-holiday-dates"),
    ("West Northamptonshire", "East Midlands", "https://www.westnorthants.gov.uk/schools-and-education/school-term-and-holiday-dates"),
    ("Nottingham", "East Midlands", "https://www.nottinghamcity.gov.uk/information-for-residents/children-young-people-and-families/schools-in-nottingham/school-term-dates/"),
    ("Nottinghamshire", "East Midlands", "https://www.nottinghamshire.gov.uk/education/school-term-and-holiday-dates"),
    ("Rutland", "East Midlands", "https://www.rutland.gov.uk/schools-children-families/term-dates"),

    # East of England
    ("Bedford", "East of England", "https://www.bedford.gov.uk/schools-education-and-childcare/schools-and-colleges/term-dates"),
    ("Cambridgeshire", "East of England", "https://www.cambridgeshire.gov.uk/residents/children-and-families/schools-learning/school-term-dates-and-holidays"),
    ("Central Bedfordshire", "East of England", "https://www.centralbedfordshire.gov.uk/info/8/schools_and_education/53/term_and_holiday_dates"),
    ("Essex", "East of England", "https://www.essex.gov.uk/schools-learning/school-term-dates"),
    ("Hertfordshire", "East of England", "https://www.hertfordshire.gov.uk/services/schools-and-education/term-dates-and-school-holidays/term-dates-and-school-holidays.aspx"),
    ("Luton", "East of England", "https://m.luton.gov.uk/Page/Show/Education_and_learning/schools/school_term_dates/Pages/default.aspx"),
    ("Norfolk", "East of England", "https://www.norfolk.gov.uk/education-and-learning/schools/school-holiday-dates"),
    ("Peterborough", "East of England", "https://www.peterborough.gov.uk/residents/schools-and-education/school-term-dates"),
    ("Southend-on-Sea", "East of England", "https://www.southend.gov.uk/term-dates"),
    ("Suffolk", "East of England", "https://www.suffolk.gov.uk/children-families-and-learning/schools/school-term-and-holiday-dates"),
    ("Thurrock", "East of England", "https://www.thurrock.gov.uk/term-dates"),

    # London
    ("Barking and Dagenham", "London", "https://www.lbbd.gov.uk/school-term-dates"),
    ("Barnet", "London", "https://www.barnet.gov.uk/schools-and-education/school-life/school-term-dates"),
    ("Bexley", "London", "https://www.bexley.gov.uk/services/schools-and-education/term-dates-and-school-closures"),
    ("Brent", "London", "https://www.brent.gov.uk/schools-and-education/school-term-dates"),
    ("Bromley", "London", "https://www.bromley.gov.uk/schools-term-dates"),
    ("Camden", "London", "https://www.camden.gov.uk/term-dates"),
    ("City of London", "London", "https://www.cityoflondon.gov.uk/services/education/schools"),
    ("Croydon", "London", "https://www.croydon.gov.uk/schools-and-education/school-term-dates-and-holidays"),
    ("Ealing", "London", "https://www.ealing.gov.uk/info/201007/schools/489/term_dates"),
    ("Enfield", "London", "https://www.enfield.gov.uk/services/schools-and-education/term-dates"),
    ("Greenwich", "London", "https://www.royalgreenwich.gov.uk/info/200221/schools/229/school_term_dates_and_inset_days"),
    ("Hackney", "London", "https://education.hackney.gov.uk/content/term-dates"),
    ("Hammersmith and Fulham", "London", "https://www.lbhf.gov.uk/schools/school-term-dates"),
    ("Haringey", "London", "https://www.haringey.gov.uk/children-and-families/schools-and-education/term-dates"),
    ("Harrow", "London", "https://www.harrow.gov.uk/schools-learning/school-term-holiday-dates"),
    ("Havering", "London", "https://www.havering.gov.uk/info/20009/schools_and_learning/220/school_term_dates"),
    ("Hillingdon", "London", "https://www.hillingdon.gov.uk/schoolterms"),
    ("Hounslow", "London", "https://www.hounslow.gov.uk/info/20040/schools_and_education/64/term_and_holiday_dates"),
    ("Islington", "London", "https://www.islington.gov.uk/children-and-families/schools/term-dates"),
    ("Kensington and Chelsea", "London", "https://www.rbkc.gov.uk/schools-education/school-life/school-term-and-holiday-dates"),
    ("Kingston upon Thames", "London", "https://www.kingston.gov.uk/term-dates-school-closures"),
    ("Lambeth", "London", "https://www.lambeth.gov.uk/schools-education/term-dates-school-closures"),
    ("Lewisham", "London", "https://lewisham.gov.uk/myservices/education/schools/term-dates"),
    ("Merton", "London", "https://www.merton.gov.uk/schools-and-education/term-dates"),
    ("Newham", "London", "https://www.newham.gov.uk/children-families/term-dates"),
    ("Redbridge", "London", "https://www.redbridge.gov.uk/schools-and-education/school-term-dates/"),
    ("Richmond upon Thames", "London", "https://www.richmond.gov.uk/services/schools/school_term_and_holiday_dates"),
    ("Southwark", "London", "https://www.southwark.gov.uk/schools-and-education/term-dates"),
    ("Sutton", "London", "https://www.sutton.gov.uk/info/200439/schools_and_education/1366/school_term_dates"),
    ("Tower Hamlets", "London", "https://www.towerhamlets.gov.uk/lgnl/education_and_learning/schools/term_dates.aspx"),
    ("Waltham Forest", "London", "https://www.walthamforest.gov.uk/schools-and-education/term-dates-school-holidays-and-inset-days"),
    ("Wandsworth", "London", "https://www.wandsworth.gov.uk/schools-and-education/school-term-dates/"),
    ("Westminster", "London", "https://www.westminster.gov.uk/schools-libraries-and-leisure/schools-term-dates"),

    # North East
    ("County Durham", "North East", "https://www.durham.gov.uk/termdates"),
    ("Darlington", "North East", "https://www.darlington.gov.uk/education-and-learning/schools/school-term-dates/"),
    ("Gateshead", "North East", "https://www.gateshead.gov.uk/article/2655/School-term-and-holiday-dates"),
    ("Hartlepool", "North East", "https://www.hartlepool.gov.uk/info/20025/schools_and_colleges/161/school_term_and_holiday_dates"),
    ("Middlesbrough", "North East", "https://www.middlesbrough.gov.uk/schools-education/school-term-dates/"),
    ("Newcastle upon Tyne", "North East", "https://www.newcastle.gov.uk/services/schools-and-learning/school-life/term-and-holiday-dates"),
    ("North Tyneside", "North East", "https://my.northtyneside.gov.uk/category/1216/term-and-holiday-dates"),
    ("Northumberland", "North East", "https://www.northumberland.gov.uk/Education/Schools/Schools-information.aspx"),
    ("Redcar and Cleveland", "North East", "https://www.redcar-cleveland.gov.uk/schools-and-education/term-dates"),
    ("South Tyneside", "North East", "https://www.southtyneside.gov.uk/article/35110/School-term-and-holiday-dates"),
    ("Stockton-on-Tees", "North East", "https://www.stockton.gov.uk/article/2068/School-term-and-holiday-dates"),
    ("Sunderland", "North East", "https://www.sunderland.gov.uk/article/12459/School-term-dates"),

    # North West
    ("Blackburn with Darwen", "North West", "https://www.blackburn.gov.uk/schools-and-education/school-term-dates"),
    ("Blackpool", "North West", "https://www.blackpool.gov.uk/Residents/Education-and-schools/School-term-dates.aspx"),
    ("Bolton", "North West", "https://www.bolton.gov.uk/school-term-dates"),
    ("Bury", "North West", "https://www.bury.gov.uk/index.aspx?articleid=12082"),
    ("Cheshire East", "North West", "https://www.cheshireeast.gov.uk/schools/term_dates/term-dates.aspx"),
    ("Cheshire West and Chester", "North West", "https://www.cheshirewestandchester.gov.uk/residents/education-and-learning/term-dates"),
    ("Cumberland", "North West", "https://www.cumberland.gov.uk/schools-education/school-term-dates"),
    ("Halton", "North West", "https://www.halton.gov.uk/childrenandfamilies/Schools/SchoolTermsHolidayDates"),
    ("Knowsley", "North West", "https://www.knowsley.gov.uk/residents/education-and-schools/term-dates-school-holidays-and-inset-days"),
    ("Lancashire", "North West", "https://www.lancashire.gov.uk/children-education-families/schools/school-term-and-holiday-dates/"),
    ("Liverpool", "North West", "https://liverpool.gov.uk/schools-and-learning/school-term-dates/"),
    ("Manchester", "North West", "https://secure.manchester.gov.uk/info/100009/schools_and_universities/4942/school_term_holiday_and_closure_dates"),
    ("Oldham", "North West", "https://www.oldham.gov.uk/info/200221/schools/2218/school_term_and_holiday_dates"),
    ("Rochdale", "North West", "https://www.rochdale.gov.uk/schools-and-education/term-dates-and-school-holidays"),
    ("Salford", "North West", "https://www.salford.gov.uk/schools-and-learning/school-term-dates-and-holidays/"),
    ("Sefton", "North West", "https://www.sefton.gov.uk/schools-learning/school-term-dates"),
    ("St Helens", "North West", "https://www.sthelens.gov.uk/article/4033/School-term-and-holiday-dates"),
    ("Stockport", "North West", "https://www.stockport.gov.uk/topic/term-and-holiday-dates"),
    ("Tameside", "North West", "https://www.tameside.gov.uk/schoolholidaydates"),
    ("Trafford", "North West", "https://www.trafford.gov.uk/residents/schools/inset-and-term-dates.aspx"),
    ("Warrington", "North West", "https://www.warrington.gov.uk/schools-term-dates"),
    ("Westmorland and Furness", "North West", "https://www.westmorlandandfurness.gov.uk/schools-and-learning/school-term-and-holiday-dates"),
    ("Wigan", "North West", "https://www.wigan.gov.uk/Resident/Education/Schools/School-Term-Dates.aspx"),
    ("Wirral", "North West", "https://www.wirral.gov.uk/schools-and-learning/school-term-dates-holidays-and-closures"),

    # South East
    ("Bracknell Forest", "South East", "https://www.bracknell-forest.gov.uk/schools-learning/term-and-holiday-dates"),
    ("Brighton and Hove", "South East", "https://www.brighton-hove.gov.uk/children-and-families/family-life/schools/term-dates"),
    ("Buckinghamshire", "South East", "https://www.buckinghamshire.gov.uk/schools-and-learning/state-school-term-and-holiday-dates/"),
    ("East Sussex", "South East", "https://www.eastsussex.gov.uk/educationlearning/schools/about/calendar"),
    ("Hampshire", "South East", "https://www.hants.gov.uk/educationandlearning/schoolsandcolleges/termdates"),
    ("Isle of Wight", "South East", "https://www.iow.gov.uk/azservices/schools-and-education/term-dates/"),
    ("Kent", "South East", "https://www.kent.gov.uk/education-and-children/schools/term-dates-and-holidays"),
    ("Medway", "South East", "https://www.medway.gov.uk/info/200137/schools_and_education/238/school_term_dates_and_holidays"),
    ("Milton Keynes", "South East", "https://www.milton-keynes.gov.uk/schools-and-lifelong-learning/school-term-dates"),
    ("Oxfordshire", "South East", "https://www.oxfordshire.gov.uk/residents/schools/term-dates-and-school-holidays"),
    ("Portsmouth", "South East", "https://www.portsmouth.gov.uk/services/schools-and-education/school-term-dates/"),
    ("Reading", "South East", "https://www.reading.gov.uk/schools-and-education/term-dates/"),
    ("Slough", "South East", "https://www.slough.gov.uk/schools-learning/school-term-dates-school-year"),
    ("Southampton", "South East", "https://www.southampton.gov.uk/schools-learning/school-life/school-term-dates/"),
    ("Surrey", "South East", "https://www.surreycc.gov.uk/schools-and-learning/schools/term-dates-and-holidays"),
    ("West Berkshire", "South East", "https://info.westberks.gov.uk/termdates"),
    ("West Sussex", "South East", "https://www.westsussex.gov.uk/education-children-and-families/schools-and-colleges/term-dates/"),
    ("Windsor and Maidenhead", "South East", "https://www.rbwm.gov.uk/home/schools-and-education/school-term-dates"),
    ("Wokingham", "South East", "https://www.wokingham.gov.uk/schools-and-learning/term-dates-and-school-holidays/"),

    # South West
    ("Bath and North East Somerset", "South West", "https://www.bathnes.gov.uk/services/schools-colleges-and-learning/school-term-and-holiday-dates"),
    ("Bournemouth, Christchurch and Poole", "South West", "https://www.bcpcouncil.gov.uk/Children-and-families/Schools-and-learning/Schools/Term-dates-and-school-holidays.aspx"),
    ("Bristol", "South West", "https://www.bristol.gov.uk/residents/schools-learning-and-early-years/find-a-school/term-and-holiday-dates"),
    ("Cornwall", "South West", "https://www.cornwall.gov.uk/schools-and-education/schools-and-colleges/term-dates/"),
    ("Devon", "South West", "https://www.devon.gov.uk/educationandfamilies/school-information/term-dates"),
    ("Dorset", "South West", "https://www.dorsetcouncil.gov.uk/education-and-children/schools-and-learning/school-term-dates-and-school-holidays"),
    ("Gloucestershire", "South West", "https://www.gloucestershire.gov.uk/education-and-learning/school-term-and-holiday-dates/"),
    ("Isles of Scilly", "South West", "https://www.scilly.gov.uk/schools-and-childrens-services/school-term-dates"),
    ("North Somerset", "South West", "https://www.n-somerset.gov.uk/my-services/schools-learning/schools-services/school-term-and-holiday-dates"),
    ("Plymouth", "South West", "https://www.plymouth.gov.uk/term-dates"),
    ("Somerset", "South West", "https://www.somerset.gov.uk/schools-and-learning/school-term-and-holiday-dates/"),
    ("South Gloucestershire", "South West", "https://www.southglos.gov.uk/children-young-people-and-families/schools-and-learning/term-dates/"),
    ("Swindon", "South West", "https://www.swindon.gov.uk/info/20066/schools/297/term_dates_and_school_holidays"),
    ("Torbay", "South West", "https://www.torbay.gov.uk/schools-and-learning/schools/term-dates/"),
    ("Wiltshire", "South West", "https://www.wiltshire.gov.uk/article/952/School-term-and-holiday-dates"),

    # West Midlands
    ("Birmingham", "West Midlands", "https://www.birmingham.gov.uk/info/20029/schools/430/school_term_dates_and_holidays"),
    ("Coventry", "West Midlands", "https://www.coventry.gov.uk/info/19/schools_in_coventry/2080/school_term_dates_and_holidays"),
    ("Dudley", "West Midlands", "https://www.dudley.gov.uk/resident/learning-school/school-life-and-holidays/school-term-dates/"),
    ("Herefordshire", "West Midlands", "https://www.herefordshire.gov.uk/info/200200/schools/250/school_term_dates"),
    ("Sandwell", "West Midlands", "https://www.sandwell.gov.uk/info/200298/schools_and_education/2247/school_term_dates"),
    ("Shropshire", "West Midlands", "https://www.shropshire.gov.uk/schools-and-education/school-and-college-information/school-term-dates/"),
    ("Solihull", "West Midlands", "https://www.solihull.gov.uk/Education-and-learning/School-term-and-holiday-dates"),
    ("Staffordshire", "West Midlands", "https://www.staffordshire.gov.uk/Education/Educationoffer/School-term-and-holiday-dates.aspx"),
    ("Stoke-on-Trent", "West Midlands", "https://www.stoke.gov.uk/info/20094/term_dates"),
    ("Telford and Wrekin", "West Midlands", "https://www.telford.gov.uk/info/20070/schools_and_education/3144/school_term_dates"),
    ("Walsall", "West Midlands", "https://go.walsall.gov.uk/education/school-information/school-term-and-holiday-dates"),
    ("Warwickshire", "West Midlands", "https://www.warwickshire.gov.uk/schoolterm"),
    ("Wolverhampton", "West Midlands", "https://www.wolverhampton.gov.uk/education-and-learning/term-dates"),
    ("Worcestershire", "West Midlands", "https://www.worcestershire.gov.uk/schools-and-education/school-term-and-holiday-dates"),

    # Yorkshire and the Humber
    ("Barnsley", "Yorkshire and the Humber", "https://www.barnsley.gov.uk/services/schools-and-education/term-dates-and-holidays/"),
    ("Bradford", "Yorkshire and the Humber", "https://www.bradford.gov.uk/education-and-skills/school-term-dates/school-term-dates/"),
    ("Calderdale", "Yorkshire and the Humber", "https://www.calderdale.gov.uk/v2/residents/education-and-learning/schools/school-term-dates"),
    ("Doncaster", "Yorkshire and the Humber", "https://www.doncaster.gov.uk/services/schools/school-term-dates"),
    ("East Riding of Yorkshire", "Yorkshire and the Humber", "https://www.eastriding.gov.uk/learning/schools-colleges-and-academies/school-term-dates/"),
    ("Kingston upon Hull", "Yorkshire and the Humber", "https://www.hull.gov.uk/schools-and-learning/school-term-dates"),
    ("Kirklees", "Yorkshire and the Humber", "https://www.kirklees.gov.uk/beta/schools-and-childcare/term-dates.aspx"),
    ("Leeds", "Yorkshire and the Humber", "https://www.leeds.gov.uk/schools-and-education/school-term-dates"),
    ("North East Lincolnshire", "Yorkshire and the Humber", "https://www.nelincs.gov.uk/children-families-and-schools/school-term-dates/"),
    ("North Lincolnshire", "Yorkshire and the Humber", "https://www.northlincs.gov.uk/schools-libraries-and-learning/schools-colleges-and-further-education/school-term-dates/"),
    ("North Yorkshire", "Yorkshire and the Humber", "https://www.northyorks.gov.uk/education-and-learning/school-term-and-holiday-dates"),
    ("Rotherham", "Yorkshire and the Humber", "https://www.rotherham.gov.uk/schools-education/school-term-dates"),
    ("Sheffield", "Yorkshire and the Humber", "https://www.sheffield.gov.uk/schools-childcare/term-dates-school-holidays"),
    ("Wakefield", "Yorkshire and the Humber", "https://www.wakefield.gov.uk/schools-and-children/schools/term-dates-and-holidays/"),
    ("York", "Yorkshire and the Humber", "https://www.york.gov.uk/schools/term-dates"),
)
