TIRAMISU_NOISE_SLUGS = [
    "noise-tiramisu-giallozafferano",
    "noise-tiramisu_nutella-giallozafferano",
    "noise-tiramisu_pistacchio-giallozafferano",
    "noise-tiramisu_senza_uova-giallozafferano",
]


EVAL_QUESTIONS = [
    {
        "question": "Which document talks about AVPN's 63% hydration dough for Pizza Margherita?",
        "expected_slug": "pizza-margherita",
        "region_hint": "Campania",
    },
    {
        "question": "Show me the guide that cites basil torn post-bake for the Naples classic pie.",
        "expected_slug": "pizza-margherita",
        "region_hint": "Campania",
    },
    {
        "question": "Where can I find fermentation logs for dough balls resting 18 hours in Campania?",
        "expected_slug": "pizza-margherita",
        "region_hint": "Campania",
    },
    {
        "question": "Which article contains hydration comparisons between Margherita pizza and focaccia?",
        "expected_slug": "focaccia-ligure",
        "region_hint": "Liguria",
    },
    {
        "question": "Find the Ligurian piece explaining brine baths and olive oil dimples for focaccia.",
        "expected_slug": "focaccia-ligure",
        "region_hint": "Liguria",
    },
    {
        "question": "I'm in Genova: surface brining instructions for focaccia please.",
        "expected_slug": "focaccia-ligure",
        "region_hint": "Liguria",
    },
    {
        "question": "Need the dossier that logs basil oxidation rates for pesto in mortar vs blender.",
        "expected_slug": "pesto-alla-genovese",
        "region_hint": "Liguria",
    },
    {
        "question": "Which article quotes the Consorzio del Pesto Genovese lab about pine nut sourcing?",
        "expected_slug": "pesto-alla-genovese",
        "region_hint": "Liguria",
    },
    {
        "question": "Where is the local report about marble mortar RPM caps for pesto alla Genovese?",
        "expected_slug": "pesto-alla-genovese",
        "region_hint": "Liguria",
    },
    {
        "question": "Point me to the risotto study referencing saffron pistils logged in Milano labs.",
        "expected_slug": "risotto-alla-milanese",
        "region_hint": "Lombardia",
    },
    {
        "question": "Which local document ties Risotto alla Milanese to tram vibration mitigation stats?",
        "expected_slug": "risotto-alla-milanese",
        "region_hint": "Lombardia",
    },
    {
        "question": "Looking for the risotto sheet with ossobuco pairing telemetry.",
        "expected_slug": "risotto-alla-milanese",
        "region_hint": "Lombardia",
    },
    {
        "question": "Where's the Milan dataset tracking saffron bloom dates for panettone starters?",
        "expected_slug": "panettone-milanese",
        "region_hint": "Lombardia",
    },
    {
        "question": "Need the panettone brief documenting lievito madre refresh rates before Christmas.",
        "expected_slug": "panettone-milanese",
        "region_hint": "Lombardia",
    },
    {
        "question": "Show the Milanese article that links panettone crumb porosity with humidity sensors.",
        "expected_slug": "panettone-milanese",
        "region_hint": "Lombardia",
    },
    {
        "question": "What article details Bergamo's bronze paiolo stirring cadence for polenta?",
        "expected_slug": "polenta-bergamasca",
        "region_hint": "Lombardia",
    },
    {
        "question": "Find the document citing thermal cameras for Bergamasca polenta texture.",
        "expected_slug": "polenta-bergamasca",
        "region_hint": "Lombardia",
    },
    {
        "question": "Which write-up includes civic archives about polenta taragna grain blends?",
        "expected_slug": "polenta-bergamasca",
        "region_hint": "Lombardia",
    },
    {
        "question": "I need the Lazio article measuring guanciale rendering curves for carbonara.",
        "expected_slug": "spaghetti-carbonara",
        "region_hint": "Lazio",
    },
    {
        "question": "Which carbonara piece references Rome's Trastevere panel tasting notes?",
        "expected_slug": "spaghetti-carbonara",
        "region_hint": "Lazio",
    },
    {
        "question": "Show me the document discouraging cream in carbonara but logging pecorino batches.",
        "expected_slug": "spaghetti-carbonara",
        "region_hint": "Lazio",
    },
    {
        "question": "Where is the Saltimbocca research quoting Turismo Roma on veal traceability?",
        "expected_slug": "saltimbocca-romana",
        "region_hint": "Lazio",
    },
    {
        "question": "Which Lazio brief compares sage leaf placement for saltimbocca performance?",
        "expected_slug": "saltimbocca-romana",
        "region_hint": "Lazio",
    },
    {
        "question": "Show documentation about PDO prosciutto sourcing for saltimbocca in Rome.",
        "expected_slug": "saltimbocca-romana",
        "region_hint": "Lazio",
    },
    {
        "question": "Need the Bologna article that logs lamination torque for lasagna sfoglia.",
        "expected_slug": "lasagna-bolognese",
        "region_hint": "Emilia-Romagna",
    },
    {
        "question": "Find the lasagna file citing Modena's triple-decker DOC layering rules.",
        "expected_slug": "lasagna-bolognese",
        "region_hint": "Emilia-Romagna",
    },
    {
        "question": "Where is the ravioli paper listing ricotta moisture audits in Parma?",
        "expected_slug": "ravioli-ricotta-spinaci",
        "region_hint": "Emilia-Romagna",
    },
    {
        "question": "Which document covers leaf spinach blanch curves for ricotta ravioli fillings?",
        "expected_slug": "ravioli-ricotta-spinaci",
        "region_hint": "Emilia-Romagna",
    },
    {
        "question": "Need the Emilia primer linking ravioli crimps to boiling turbulence data.",
        "expected_slug": "ravioli-ricotta-spinaci",
        "region_hint": "Emilia-Romagna",
    },
    {
        "question": "Point me to the Genoa minestrone note about soaked beans and basil steam traps.",
        "expected_slug": "minestrone-genovese",
        "region_hint": "Liguria",
    },
    {
        "question": "Find the soup article citing Maritime Alps climate data in a vegetable broth table.",
        "expected_slug": "minestrone-genovese",
        "region_hint": "Liguria",
    },
    {
        "question": "Where can I read about buffalo mozzarella double draining for Caprese salad?",
        "expected_slug": "insalata-caprese",
        "region_hint": "Campania",
    },
    {
        "question": "Need the Caprese insight on 12°Brix checks for tomatoes in Capri.",
        "expected_slug": "insalata-caprese",
        "region_hint": "Campania",
    },
    {
        "question": "Show me the Capri post that logs basil transpiration tests for salad plating.",
        "expected_slug": "insalata-caprese",
        "region_hint": "Campania",
    },
    {
        "question": "Which Treviso dossier explains mascarpone fat percentages for tiramisù?",
        "expected_slug": "tiramisu-treviso",
        "region_hint": "Veneto",
    },
    {
        "question": "Find the tiramisù report that references pH thresholds for raw eggs in Treviso.",
        "expected_slug": "tiramisu-treviso",
        "region_hint": "Veneto",
    },
    {
        "question": "Where is the document logging cocoa dust granulometry for tiramisù service?",
        "expected_slug": "tiramisu-treviso",
        "region_hint": "Veneto",
    },
    {
        "question": "Need the Sicilian brief citing orange blossom water in cannoli shells.",
        "expected_slug": "cannoli-siciliani",
        "region_hint": "Sicilia",
    },
    {
        "question": "Which article documents ricotta aeration percentages for cannoli filling?",
        "expected_slug": "cannoli-siciliani",
        "region_hint": "Sicilia",
    },
    {
        "question": "Show me the cannoli story referencing fry oil turnover in Palermo labs.",
        "expected_slug": "cannoli-siciliani",
        "region_hint": "Sicilia",
    },
    {
        "question": "Where can I read about arancini cone molds tested in Catania?",
        "expected_slug": "arancini-siciliani",
        "region_hint": "Sicilia",
    },
    {
        "question": "Need the document comparing ragù fillings vs pistachio for Sicilian arancini.",
        "expected_slug": "arancini-siciliani",
        "region_hint": "Sicilia",
    },
    {
        "question": "Which local article logs frying oil refresh cycles for arancini stands?",
        "expected_slug": "arancini-siciliani",
        "region_hint": "Sicilia",
    },
    {
        "question": "Find the Osso Buco page quoting marrow temperature at service.",
        "expected_slug": "osso-buco",
        "region_hint": "Lombardia",
    },
    {
        "question": "Where is the Lombardy article pairing osso buco with gremolata sensor data?",
        "expected_slug": "osso-buco",
        "region_hint": "Lombardia",
    },
    {
        "question": "Need the veal shank briefing that references Milan hospital menus from the 1800s.",
        "expected_slug": "osso-buco",
        "region_hint": "Lombardia",
    },
    {
        "question": "Which document covers bistecca Fiorentina searing curves monitored in Chianti?",
        "expected_slug": "bistecca-fiorentina",
        "region_hint": "Toscana",
    },
    {
        "question": "Show me the Tuscan post that logs dry-aging humidity for bistecca.",
        "expected_slug": "bistecca-fiorentina",
        "region_hint": "Toscana",
    },
    {
        "question": "Where can I find gelato Fiorentino overrun percentages from Via dei Neri labs?",
        "expected_slug": "gelato-fiorentino",
        "region_hint": "Toscana",
    },
    {
        "question": "Find the document discussing potato gnocchi starch indexes in Trentino labs.",
        "expected_slug": "gnocchi-di-patate",
        "region_hint": "Trentino-Alto Adige",
    }
]

# Structured-data & negative-bias questions
EVAL_QUESTIONS.extend(
    [
        {
            "question": "Which FAQ explains pasteurizing yolks to 72°C for tiramisù safety?",
            "expected_slug": "tiramisu-treviso",
            "region_hint": "Veneto",
            "top_n": 5,
        },
        {
            "question": "Which tiramisù FAQ answers 'Which alcohol works best?'",
            "expected_slug": "tiramisu-treviso",
            "region_hint": "Veneto",
            "top_n": 5,
        },
        {
            "question": "Which document lists 500 g mascarpone at 45% fat in its ingredients?",
            "expected_slug": "tiramisu-treviso",
            "region_hint": "Veneto",
            "top_n": 5,
        },
        {
            "question": "I need a Margherita hydration brief (no desserts).",
            "expected_slug": "pizza-margherita",
            "region_hint": "Campania",
            "forbidden_slugs": TIRAMISU_NOISE_SLUGS,
        },
        {
            "question": "Point me to a carbonara telemetry report—not a tiramisù.",
            "expected_slug": "spaghetti-carbonara",
            "region_hint": "Lazio",
            "forbidden_slugs": TIRAMISU_NOISE_SLUGS,
        },
        {
            "question": "Is there any tiramisù made with porcini mushrooms?",
            "expected_slug": None,
            "forbidden_slugs": ["tiramisu-treviso", *TIRAMISU_NOISE_SLUGS],
            "require_empty": False,
            "top_n": 5,
        },
    ]
)
