"""Seed published sample articles for environments that cannot scrape RSS (e.g. free PA)."""
from datetime import timedelta
from pathlib import Path

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import Role, User
from authors.models import AuthorProfile
from categories.models import Category, Tag
from news.models import Article
from news.services import ArticleService
from news.utils.images import optimize_image_bytes
from news.utils.placeholders import assign_hero_image, generate_placeholder_image


SAMPLE_ARTICLES = [
    {
        'title': 'Iloilo City expands riverside walkways to boost tourism and local trade',
        'category': 'Regional News',
        'province': 'Iloilo',
        'featured': True,
        'sticky': True,
        'breaking': False,
        'editors_pick': True,
        'image_seed': 'iloilo-river',
        'photo_url': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'City planners unveiled a multi-phase riverside project aimed at safer pedestrian '
            'access, greener public spaces, and stronger support for nearby small businesses '
            'along Iloilo’s busiest waterfront corridors.'
        ),
        'body': [
            'ILOILO CITY — Local officials formally launched an expanded riverside walkway '
            'program designed to improve mobility along the city’s waterfront districts and '
            'create a more welcoming environment for residents and visitors alike.',
            'The plan includes wider pedestrian lanes, improved lighting, shaded rest areas, '
            'clearer wayfinding signs, and new seating pockets near popular viewing points. '
            'Officials said the design also leaves room for emergency vehicle access.',
            'Business groups welcomed the move, saying better foot traffic could help cafes, '
            'souvenir shops, transport terminals, and weekend market vendors around the '
            'Esplanade corridor and nearby heritage streets.',
            'City engineers said construction will proceed in phases to limit disruption, with '
            'priority given to high-traffic stretches used by students, joggers, and evening '
            'commuters. Temporary detours will be posted at least one week in advance.',
            'Environmental officers added that soft landscaping and permeable surfaces are '
            'part of the package, hoping to reduce heat along open stretches and improve '
            'drainage during heavy rains.',
            'Tourism stakeholders said the upgraded walkways could strengthen Iloilo’s appeal '
            'as a stopover city for domestic travelers exploring Western Visayas, especially '
            'when paired with food tours and river-cruise activities.',
            'Community consultations will continue in the affected barangays, with feedback '
            'desks open at the city hall annex and selected barangay centers throughout the '
            'first construction phase.',
        ],
    },
    {
        'title': 'Western Visayas schools roll out digital literacy modules for senior high',
        'category': 'Education',
        'province': 'Western Visayas',
        'featured': True,
        'sticky': False,
        'breaking': False,
        'editors_pick': True,
        'image_seed': 'education-tech',
        'photo_url': 'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Regional education offices introduced classroom modules on online safety, media '
            'literacy, and basic coding for senior high students across Western Visayas, with '
            'teacher coaching sessions scheduled through the school year.'
        ),
        'body': [
            'Education supervisors across Western Visayas began distributing digital literacy '
            'modules intended to help senior high students navigate online information more '
            'carefully and use classroom technology with greater confidence.',
            'Teachers received orientation sessions covering responsible social media use, '
            'spotting misleading content, privacy basics, and introductory computational '
            'thinking exercises that can be taught with or without constant internet access.',
            'School heads said the materials are designed for both urban and rural campuses, '
            'including printable activity sheets for classrooms that still rely on shared '
            'computer laboratories.',
            'Guidance counselors welcomed the focus on online safety, noting that students '
            'increasingly encounter unverified claims, aggressive comment threads, and '
            'pressure to share personal information.',
            'Regional trainers plan follow-up visits to monitor classroom adoption and gather '
            'feedback from students before expanding optional coding electives next semester.',
            'Parents’ associations were invited to evening briefings so households can reinforce '
            'the same digital habits at home, especially around screen time and source checking.',
        ],
    },
    {
        'title': 'Negros farmers adopt climate-ready rice varieties ahead of wet season',
        'category': 'Business',
        'province': 'Negros Occidental',
        'featured': True,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'rice-farm',
        'photo_url': 'https://images.unsplash.com/photo-1625246333195-78d9c38ad449?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Agricultural cooperatives in Negros Occidental are shifting to climate-ready rice '
            'strains as forecasts point to uneven rainfall through the coming planting months, '
            'with extension teams offering seed support and field demos.'
        ),
        'body': [
            'BACOLOD CITY — Farmer cooperatives reported early adoption of climate-ready rice '
            'varieties recommended by regional agriculture offices ahead of the wet-season '
            'planting window.',
            'Extension workers said the seeds are better suited for periods of heavy rain and '
            'short dry spells that have become more common in recent seasons, reducing the risk '
            'of crop stress during critical growth stages.',
            'Local traders expect stable supply if planting schedules stay on track, though '
            'transport costs remain a concern for inland municipalities that rely on longer '
            'hauling routes to major markets.',
            'Cooperative leaders asked for continued access to affordable fertilizer packages '
            'and clearer weather advisories so members can time irrigation and harvesting more '
            'effectively.',
            'Demo farms in selected towns will compare yields between traditional and '
            'climate-ready varieties, with results scheduled for sharing before the next '
            'planting cycle.',
            'Agriculture officers emphasized that seed distribution is only one part of the '
            'strategy, pairing it with soil testing, pest monitoring, and post-harvest handling '
            'tips for smallholder families.',
        ],
    },
    {
        'title': 'Global markets steady as tech earnings calm investor nerves',
        'category': 'International',
        'province': '',
        'featured': True,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'global-markets',
        'photo_url': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Major indexes held firm after leading technology firms posted stronger-than-expected '
            'results, easing fears of a sharper slowdown in global demand while traders watched '
            'inflation data for the next policy clue.'
        ),
        'body': [
            'International markets opened on a steadier note after a cluster of technology earnings '
            'reports reassured investors about corporate spending, cloud demand, and consumer '
            'electronics outlooks in key economies.',
            'Analysts said the rebound remains fragile, with attention now shifting to inflation '
            'prints, employment figures, and central bank guidance in the weeks ahead.',
            'Currency traders also watched Asian markets for signals on export outlook and '
            'commodity prices tied to manufacturing activity, especially in electronics and '
            'energy-linked supply chains.',
            'Fund managers described the session as a relief rally rather than a broad risk-on '
            'shift, noting that bond yields and oil prices still have the capacity to unsettle '
            'equity sentiment quickly.',
            'For Philippine investors, remittance flows and peso movements remain important '
            'side stories, particularly for households and firms with overseas income or '
            'imported inputs.',
            'Market strategists advised clients to stay selective, favoring companies with clear '
            'cash flow visibility while treating short-term index swings as noise until clearer '
            'macro data arrives.',
        ],
    },
    {
        'title': 'Health centers push free hypertension screening in barangay clinics',
        'category': 'Health',
        'province': 'Iloilo',
        'featured': False,
        'sticky': False,
        'breaking': True,
        'editors_pick': False,
        'image_seed': 'health-clinic',
        'photo_url': 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Municipal health offices launched weekend hypertension screening in barangay clinics '
            'to catch high blood pressure cases earlier among older residents and workers with '
            'limited weekday clinic access.'
        ),
        'body': [
            'Barangay health workers began offering free blood-pressure checks and counseling '
            'sessions as part of a weekend community screening drive across selected Iloilo '
            'municipalities.',
            'Doctors involved in the campaign said early detection remains one of the most '
            'effective ways to reduce stroke and heart-related emergencies, especially among '
            'adults who feel well and skip routine checkups.',
            'Residents were also given printed guides on low-salt meals, walking routines, and '
            'medication reminders for those already under treatment.',
            'Nurses reported longer queues in the morning hours, prompting organizers to open '
            'additional tables and invite volunteer students from local nursing programs.',
            'Health officers stressed that screening is only the first step, with referral slips '
            'prepared for patients whose readings repeatedly fall outside safe ranges.',
            'Community leaders asked for the campaign to return monthly, saying weekend schedules '
            'make it easier for market vendors and construction workers to participate.',
        ],
    },
    {
        'title': 'Local startups pitch logistics tools at regional tech meetup',
        'category': 'Technology',
        'province': 'Western Visayas',
        'featured': True,
        'sticky': False,
        'breaking': False,
        'editors_pick': True,
        'image_seed': 'startup-pitch',
        'photo_url': 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Founders from Iloilo and Bacolod presented delivery-routing and inventory apps at a '
            'regional meetup focused on practical tools for small retailers, couriers, and '
            'neighborhood suppliers.'
        ),
        'body': [
            'A regional technology meetup spotlighted logistics and retail software built by '
            'Western Visayas startups for neighborhood stores, courier partners, and warehouse '
            'teams handling short-distance deliveries.',
            'Pitch sessions emphasized offline-friendly features, simple dashboards, and pricing '
            'models suited to micro and small enterprises that cannot absorb heavy subscription '
            'fees.',
            'Mentors from local incubators encouraged teams to pilot with real merchants before '
            'seeking larger funding rounds, arguing that local proof of use matters more than '
            'polished slide decks.',
            'Retailers in attendance said inventory mismatches and late last-mile drops remain '
            'daily headaches, making route optimization and stock alerts especially attractive.',
            'Organizers plan a follow-up demo day where shortlisted teams can test their tools '
            'with partner stores for 30 days and report measurable improvements.',
            'Students from nearby campuses joined as observers, with several asking how to join '
            'internship tracks tied to product support and customer onboarding.',
        ],
    },
    {
        'title': 'Provincial athletes prepare for inter-regional games in August',
        'category': 'Sports',
        'province': 'Negros Occidental',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'athletics',
        'photo_url': 'https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Training camps for athletics, swimming, and volleyball are underway as provincial '
            'delegations prepare for the August inter-regional sports meet, with coaches fine-tuning '
            'lineups and recovery schedules.'
        ),
        'body': [
            'Coaches confirmed intensified training schedules for athletes selected to represent '
            'their provinces in the coming inter-regional games, balancing skill drills with '
            'injury-prevention routines.',
            'Organizers said venues are being inspected for safety and spectator capacity, with '
            'final event lists expected before the end of the month.',
            'Swimming and athletics teams are logging early-morning sessions, while volleyball '
            'squads focus on serve receive patterns and conditioning under match-like pressure.',
            'Sports officials appealed for community support, noting that transportation, meals, '
            'and medical coverage remain the largest budget items for host and visiting teams.',
            'Young athletes said the camps also offer a chance to learn from veterans about '
            'competition nerves, nutrition, and time management during multi-day events.',
            'A short cultural program is planned alongside the opening rites to showcase host '
            'province traditions without disrupting the competition timetable.',
        ],
    },
    {
        'title': 'City council reviews flood-control timetable after heavy rains',
        'category': 'Politics',
        'province': 'Iloilo',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'flood-control',
        'photo_url': 'https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Councilors asked for clearer timelines on drainage upgrades after recent downpours '
            'flooded several low-lying barangays during peak hours, delaying school and office '
            'commutes across the city.'
        ),
        'body': [
            'Members of the city council pressed agencies for an updated flood-control timetable '
            'following repeated inundation in low-lying neighborhoods during afternoon storms.',
            'Engineering offices presented completed segments and remaining packages, including '
            'pumping stations, dredging work, and cleared waterways still under procurement.',
            'Community leaders asked for earlier public advisories whenever heavy rainfall is '
            'expected during school and office rush hours.',
            'Councilors also requested a map of the most frequently flooded intersections so '
            'traffic rerouting plans can be rehearsed with barangay responders.',
            'Residents who attended the hearing shared photos of stalled vehicles and classroom '
            'evacuations, urging faster coordination between drainage teams and schools.',
            'Officials said weekly progress bulletins will be posted online and on barangay '
            'bulletin boards until the priority segments are marked complete.',
        ],
    },
    {
        'title': 'Cultural festival returns with outdoor stages and local crafts',
        'category': 'Entertainment',
        'province': 'Western Visayas',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'festival-stage',
        'photo_url': 'https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Organizers revived an outdoor cultural festival featuring regional music, dance '
            'showcases, and craft booths from nearby municipalities, drawing families back to '
            'the open plaza for evening performances.'
        ),
        'body': [
            'Festival organizers announced the return of outdoor stages after a quieter stretch of '
            'community events, promising a fuller program of music, dance, and craft markets.',
            'This year’s lineup highlights traditional dance groups, contemporary local bands, '
            'and makers selling woven goods, pottery, and food specialties from surrounding towns.',
            'Security and medical teams will be stationed near main gates, with clear entry and '
            'exit lanes for families attending night shows.',
            'Local tourism officers said the festival helps independent artists earn weekend '
            'income while giving visitors a reason to stay overnight in nearby inns.',
            'Volunteers are being recruited for crowd assistance, stage logistics, and waste '
            'segregation so the open grounds remain usable throughout the multi-day run.',
            'A youth showcase on the final afternoon will feature student choirs and spoken-word '
            'performers selected through barangay-level auditions.',
        ],
    },
    {
        'title': 'Opinion: Why local newsrooms still matter in a viral age',
        'category': 'Opinion',
        'province': 'Philippines',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': True,
        'image_seed': 'newsroom',
        'photo_url': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'As social feeds move faster, community reporting remains essential for verifying '
            'what actually happened on the ground and giving residents context that viral posts '
            'rarely provide.'
        ),
        'body': [
            'Viral posts can travel farther than facts in a matter of minutes, which is why local '
            'newsrooms still play a critical public role in clarifying events as they unfold.',
            'Reporters who know the streets, schools, and councils of a community can challenge '
            'rumors with context that national feeds and anonymous pages often miss.',
            'Supporting credible local journalism is not nostalgia — it is infrastructure for an '
            'informed public that needs accurate information about floods, budgets, schools, and '
            'public health.',
            'Readers can help by sharing primary reporting carefully, correcting false claims '
            'when they appear in group chats, and supporting outlets that correct themselves '
            'openly when mistakes happen.',
            'Newsrooms, for their part, must keep investing in verification habits, clear '
            'sourcing, and explainers that help audiences understand not only what happened but '
            'why it matters.',
            'In a noisy information environment, trust is built slowly through consistent, '
            'transparent work — and local desks remain one of the best places to do that work.',
        ],
    },
    {
        'title': 'Weekend wellness fairs promote affordable meal planning',
        'category': 'Lifestyle',
        'province': 'Iloilo',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'wellness-fair',
        'photo_url': 'https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Community wellness fairs offered budget meal demos, short fitness sessions, and '
            'checkups aimed at busy households looking for practical health habits without '
            'raising weekly grocery costs.'
        ),
        'body': [
            'Weekend wellness fairs drew families looking for practical ways to eat better without '
            'raising weekly grocery costs or committing to expensive gym memberships.',
            'Nutrition volunteers demonstrated simple recipes using local produce, while nurses '
            'offered basic health checks at partner booths near the main stage.',
            'Fitness instructors led short walking and stretching sessions designed for beginners, '
            'including older adults who prefer low-impact routines.',
            'Organizers distributed printable meal charts with market-price estimates so families '
            'can adapt the menus to whatever vegetables are in season.',
            'Parents said the child-friendly cooking demos helped start conversations at home '
            'about snacks, water intake, and reducing sugary drinks.',
            'The fair will rotate across districts this quarter, with each stop featuring a local '
            'clinic partner and a small produce market from nearby growers.',
        ],
    },
    {
        'title': 'Transport group seeks clearer provincial bus schedule updates',
        'category': 'Regional News',
        'province': 'Western Visayas',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'bus-terminal',
        'photo_url': 'https://images.unsplash.com/photo-1570125909232-eb263c188f7e?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Commuter advocates asked terminals to post more reliable departure boards after '
            'repeated last-minute trip changes during peak weekends left passengers stranded '
            'or forced into expensive alternatives.'
        ),
        'body': [
            'Transport advocates urged provincial terminals to improve how schedule changes are '
            'announced to passengers, especially on Friday evenings and holiday weekends.',
            'Operators said they are testing digital boards and SMS advisories, though coverage '
            'still varies by terminal and signal strength inside waiting halls.',
            'Commuters described long lines forming when cancellations are announced only at the '
            'window, leaving travelers little time to rearrange plans.',
            'Advocates proposed a shared public advisory channel that all major operators can '
            'update in real time, including estimated departure windows and bay assignments.',
            'Terminal managers replied that staff training and clearer passenger signage are '
            'already in progress, with pilot boards expected at the busiest gates first.',
            'Passenger groups said they will monitor the next three peak weekends and publish a '
            'simple scorecard on whether updates arrived early enough to be useful.',
        ],
    },
    {
        'title': 'Guimaras mango growers prepare early harvest logistics',
        'category': 'Business',
        'province': 'Guimaras',
        'featured': True,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'mango-harvest',
        'photo_url': 'https://images.unsplash.com/photo-1553279768-865429fa0078?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Growers and consolidators in Guimaras are coordinating crate supply, cold-chain '
            'slots, and ferry schedules as orchards near peak harvest, hoping to reduce bruising '
            'and delays on the way to mainland markets.'
        ),
        'body': [
            'JORDAN, GUIMARAS — Mango growers began lining up harvest crews and packing materials '
            'earlier than usual after orchard managers reported uneven ripening across hillside '
            'and coastal farms.',
            'Consolidators said the biggest risks remain rough handling and ferry timing, which '
            'can turn premium fruit into lower-grade stock before it reaches Iloilo buyers.',
            'Farm cooperatives requested more reusable crates and clearer booking windows for '
            'refrigerated vans serving restaurants and grocery distributors.',
            'Agriculture technicians advised staggered picking where possible, noting that '
            'rushing the harvest during sudden rain can raise fungal losses in storage.',
            'Local tourism operators also asked for a weekend farm-gate buying schedule so '
            'visitors can purchase sorted fruit without disrupting commercial shipments.',
            'Provincial officials said they will publish a harvest advisory board at the port '
            'area listing estimated volume days and recommended handling reminders for porters.',
            'Growers emphasized that better logistics are as important as yield, because timely '
            'delivery protects both farm income and Guimaras’ reputation for quality mangoes.',
        ],
    },
    {
        'title': 'Coastal barangays drill for storm surge evacuation routes',
        'category': 'Regional News',
        'province': 'Iloilo',
        'featured': False,
        'sticky': False,
        'breaking': True,
        'editors_pick': False,
        'image_seed': 'storm-drill',
        'photo_url': 'https://images.unsplash.com/photo-1527482797697-8795b05a13fe?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Disaster-response teams walked residents through updated evacuation maps and '
            'assembly points after coastal barangays revised routes that previously crossed '
            'flood-prone roads during storm surge alerts.'
        ),
        'body': [
            'Coastal barangays conducted a full-day evacuation drill to test new routes designed '
            'to keep families away from low bridges and roads that flood quickly during surge '
            'events.',
            'Responders timed how long it took households with older adults and small children '
            'to reach designated schools and covered courts used as temporary shelters.',
            'Barangay captains said the revised maps will be posted in sari-sari stores and '
            'chapels so residents can review them before the next weather disturbance.',
            'Medical volunteers checked first-aid kits at each assembly point and noted gaps in '
            'flashlight batteries, drinking water, and patient transport stretchers.',
            'Fishers asked for clearer radio protocols when boats are still out at sea as alerts '
            'escalate, prompting a review of coastal watch assignments.',
            'Municipal DRRM officers said after-action notes from the drill will be shared with '
            'schools so classroom alerts match barangay siren and messenger announcements.',
        ],
    },
    {
        'title': 'Campus researchers test low-cost water sensors for rural taps',
        'category': 'Technology',
        'province': 'Western Visayas',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': True,
        'image_seed': 'water-sensors',
        'photo_url': 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'University teams in Western Visayas are piloting affordable water-quality sensors '
            'for barangay taps, aiming to give rural water associations faster warnings when '
            'turbidity or chlorine levels drift out of range.'
        ),
        'body': [
            'Engineering students and faculty advisers presented early field results from '
            'low-cost sensors installed on selected rural tap stands serving upland barangays.',
            'The devices track basic indicators and send simple alerts to association officers '
            'through text messages when readings stay outside preset thresholds.',
            'Water association leaders said the value is speed: instead of waiting for a weekly '
            'visit, they can dispatch a technician the same day a problem appears.',
            'Researchers cautioned that the sensors are not a replacement for laboratory tests, '
            'but a practical screening layer for associations managing limited budgets.',
            'Next trials will focus on waterproof casings, battery life during brownouts, and '
            'training modules so local technicians can calibrate units themselves.',
            'Provincial partners expressed interest in expanding the pilot if the next round '
            'shows consistent accuracy across different source types and pipe ages.',
        ],
    },
    {
        'title': 'Small hotels in Boracay adopt greener linen and waste routines',
        'category': 'Lifestyle',
        'province': 'Aklan',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'boracay-hotels',
        'photo_url': 'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Independent hotels and inns around Boracay are tightening laundry cycles, sorting '
            'rules, and supplier standards as guests increasingly ask about sustainability '
            'practices before booking.'
        ),
        'body': [
            'Hotel managers said guest questions about towels, plastics, and waste segregation '
            'have become common enough to reshape daily housekeeper briefings.',
            'Several inns now offer optional linen reuse cards and replaced miniature toiletries '
            'with refillable dispensers in renovated rooms.',
            'Waste contractors reported cleaner sorting at properties that train staff weekly '
            'and place clearer bilingual labels in service corridors.',
            'Owners noted that greener routines can lower utility costs over time, but require '
            'upfront spending on dispensers, bins, and staff coaching.',
            'Tourism officers encouraged properties to publish simple sustainability statements '
            'online so visitors can compare practices without relying on vague marketing claims.',
            'A cluster of small hotels plans a joint supplier day to negotiate better rates for '
            'biodegradable packaging and concentrated cleaning products.',
        ],
    },
    {
        'title': 'Youth debate league returns with climate and jobs themes',
        'category': 'Education',
        'province': 'Negros Occidental',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'youth-debate',
        'photo_url': 'https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Secondary schools across Negros Occidental revived an inter-campus debate league '
            'focused on climate adaptation and local employment, giving students a public stage '
            'for research-backed arguments.'
        ),
        'body': [
            'Debate coaches said interest spiked after organizers framed this season around '
            'issues students already discuss in classrooms and community youth councils.',
            'Opening rounds will cover flood preparedness, green jobs, and the role of local '
            'government in supporting first-time workers.',
            'Teachers emphasized evidence rules: teams must cite publicly available reports or '
            'interviews and avoid unsourced social-media claims.',
            'Parents and alumni were invited as timekeepers and adjudicators-in-training to '
            'broaden the pool of volunteer judges.',
            'Winning teams will advance to a provincial final that includes a short policy memo '
            'exercise, not only stage speaking.',
            'Organizers hope the league strengthens civic confidence among students who may '
            'later join campus papers, student governments, or community advocacy groups.',
        ],
    },
    {
        'title': 'Regional ports trial faster cargo appointment windows',
        'category': 'Business',
        'province': 'Western Visayas',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'cargo-port',
        'photo_url': 'https://images.unsplash.com/photo-1578575437130-527eed3abbec?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'Port operators and trucking groups began testing tighter cargo appointment windows '
            'to cut idle time at gates, with early results showing shorter queues on midweek '
            'mornings.'
        ),
        'body': [
            'Regional ports launched a pilot appointment system for selected cargo lanes after '
            'truckers complained of unpredictable waiting times that raised fuel and overtime '
            'costs.',
            'Dispatchers said digital slots help them plan driver hours more realistically, '
            'though some still want more flexibility for delayed feeder vessels.',
            'Port managers reported cleaner lane discipline when appointments are enforced with '
            'clear grace periods rather than rigid minute-by-minute cutoffs.',
            'Importers of food and construction materials watched the trial closely, hoping '
            'shorter gate times translate into steadier store replenishment.',
            'Labor representatives asked that any efficiency gains also improve rest facilities '
            'for drivers waiting through night arrivals.',
            'If midweek metrics hold, organizers may expand the appointment windows to weekend '
            'peaks after another month of monitoring.',
        ],
    },
    {
        'title': 'Public libraries add evening study hours before exams',
        'category': 'Education',
        'province': 'Iloilo',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'library-study',
        'photo_url': 'https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&w=1920&h=1080&q=80',
        'excerpt': (
            'City and municipal libraries extended evening hours in the weeks before major exams, '
            'opening quiet rooms and Wi-Fi desks for senior high and college students who lack '
            'reliable study space at home.'
        ),
        'body': [
            'Librarians said demand for evening seats rises every exam season, particularly among '
            'students sharing small homes or intermittent internet connections.',
            'Extended hours include staffed quiet rooms, device-charging corners, and short '
            'workshops on citation basics and avoiding plagiarism.',
            'Security volunteers and local police community relations teams coordinated closing '
            'time escorts for students heading to nearby terminals.',
            'Teachers encouraged classes to reserve group tables in advance so review sessions '
            'do not crowd out individual readers.',
            'Some libraries also partnered with campus writing centers for drop-in tutoring on '
            'weekends during the peak review period.',
            'City officials said they will review attendance logs before deciding whether '
            'year-round evening hours are financially sustainable.',
        ],
    },
]


class Command(BaseCommand):
    help = (
        'Create published sample articles with sharp hero images for demos '
        'and free hosting where RSS scraping is blocked'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recreate sample articles even if their slugs already exist',
        )

    def handle(self, *args, **options):
        force = options['force']
        author = self._ensure_author()
        created = 0
        updated = 0
        now = timezone.now()

        for index, item in enumerate(SAMPLE_ARTICLES):
            category, _ = Category.objects.get_or_create(
                slug=slugify(item['category']),
                defaults={'name': item['category'], 'is_active': True},
            )
            slug = slugify(item['title'])[:280]
            article = Article.objects.filter(slug=slug).first()
            if article and not force:
                if not article.hero_image:
                    self._assign_image(article, index, item)
                    updated += 1
                continue

            body_html = '\n'.join(f'<p>{paragraph}</p>' for paragraph in item['body'])
            if article and force:
                article.title = item['title']
                article.excerpt = item['excerpt']
                article.body = body_html
                article.category = category
                article.author = author
                article.province = item.get('province', '')
                article.is_featured = item.get('featured', False)
                article.is_sticky = item.get('sticky', False)
                article.is_breaking = item.get('breaking', False)
                article.is_editors_pick = item.get('editors_pick', False)
                article.status = 'published'
                article.published_at = now - timedelta(hours=index * 3)
                article.is_scraped = False
                article.verification_status = ''
                article.allow_comments = True
                ArticleService.prepare_article(article)
                article.save()
                self._assign_image(article, index, item, force=True)
                updated += 1
                self.stdout.write(f'  ~ updated {article.title}')
                continue

            article = Article(
                title=item['title'],
                slug=slug,
                excerpt=item['excerpt'],
                body=body_html,
                category=category,
                author=author,
                created_by=author.user if author else None,
                province=item.get('province', ''),
                status='published',
                published_at=now - timedelta(hours=index * 3),
                is_featured=item.get('featured', False),
                is_sticky=item.get('sticky', False),
                is_breaking=item.get('breaking', False),
                is_editors_pick=item.get('editors_pick', False),
                allow_comments=True,
                is_scraped=False,
                view_count=180 - index * 5,
            )
            ArticleService.prepare_article(article)
            article.save()

            tag_names = ['Regional', 'Community'] if item.get('province') else ['World', 'Analysis']
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(
                    slug=slugify(tag_name),
                    defaults={'name': tag_name},
                )
                article.tags.add(tag)

            self._assign_image(article, index, item)
            created += 1
            self.stdout.write(f'  + {article.title}')

        self.stdout.write(self.style.SUCCESS(
            f'Sample articles ready: {created} created, {updated} updated.'
        ))

    def _ensure_author(self) -> AuthorProfile:
        role, _ = Role.objects.get_or_create(
            name='reporter',
            defaults={'display_name': 'Reporter', 'is_staff_role': True},
        )
        user, created = User.objects.get_or_create(
            email='reporter@nextgennews.com',
            defaults={
                'username': 'reporter',
                'first_name': 'Jane',
                'last_name': 'Reporter',
                'role': role,
                'is_email_verified': True,
            },
        )
        if created:
            user.set_password('Reporter@12345')
            user.save()

        author, _ = AuthorProfile.objects.get_or_create(
            slug='jane-reporter',
            defaults={
                'user': user,
                'display_name': 'Jane Reporter',
                'biography': 'Covers regional development, education, and community affairs.',
                'job_title': 'Senior Reporter',
                'is_featured': True,
            },
        )
        return author

    def _assign_image(self, article: Article, index: int, item: dict, force: bool = False) -> None:
        samples_dir = Path(settings.BASE_DIR) / 'static' / 'img' / 'samples'
        samples_dir.mkdir(parents=True, exist_ok=True)
        path = samples_dir / f'{article.slug}.jpg'

        if path.exists() and path.stat().st_size >= 50000:
            article.hero_image.save(
                f'sample-{article.slug[:50]}.jpg',
                ContentFile(path.read_bytes()),
                save=True,
            )
            article.hero_image_caption = 'Photo illustration'
            article.save(update_fields=['hero_image_caption'])
            return

        if item.get('photo_url') and self._download_photo_url(path, item['photo_url']):
            article.hero_image.save(
                f'sample-{article.slug[:50]}.jpg',
                ContentFile(path.read_bytes()),
                save=True,
            )
            article.hero_image_caption = 'Photo illustration'
            article.save(update_fields=['hero_image_caption'])
            return

        self._write_static_sample(article, index)
        assign_hero_image(article, index=index, force=True)
        self._download_stock_image(article, item.get('image_seed', article.slug))

    def _write_static_sample(self, article: Article, index: int) -> None:
        samples_dir = Path(settings.BASE_DIR) / 'static' / 'img' / 'samples'
        samples_dir.mkdir(parents=True, exist_ok=True)
        path = samples_dir / f'{article.slug}.jpg'
        if path.exists() and path.stat().st_size > 10000:
            return
        category_name = article.category.name if article.category else 'News'
        buffer = generate_placeholder_image(article.title, category_name, index)
        path.write_bytes(buffer.read())

    def _download_photo_url(self, path: Path, url: str) -> bool:
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=40)
            response.raise_for_status()
            from io import BytesIO
            from PIL import Image

            img = Image.open(BytesIO(response.content)).convert('RGB')
            target_w, target_h = 1920, 1080
            scale = max(target_w / img.width, target_h / img.height)
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
            left = (img.width - target_w) // 2
            top = (img.height - target_h) // 2
            img = img.crop((left, top, left + target_w, top + target_h))
            buf = BytesIO()
            img.save(buf, format='JPEG', quality=90, optimize=True, progressive=True)
            path.write_bytes(buf.getvalue())
            return path.stat().st_size >= 50000
        except Exception:
            return False

    def _download_stock_image(self, article: Article, seed: str) -> bool:
        """Try a high-res public photo; ignore failures on locked-down hosts."""
        url = f'https://picsum.photos/seed/{seed}/1920/1080'
        try:
            response = requests.get(url, timeout=12, allow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type and not response.content.startswith(b'\xff\xd8'):
                return False
            optimized = optimize_image_bytes(response.content, min_width=900)
            if not optimized:
                return False
            filename = f'sample-{article.slug[:50]}.jpg'
            article.hero_image.save(filename, ContentFile(optimized), save=True)
            article.hero_image_caption = 'Sample photo for demonstration'
            article.save(update_fields=['hero_image_caption'])
            return True
        except Exception:
            return False
