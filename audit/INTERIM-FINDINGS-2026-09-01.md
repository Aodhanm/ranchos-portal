# Ranchos audit — interim findings (54 of 100 blind-sample records graded)

Verification against the Bancroft land case file PDFs, in progress. Numbers are PARTIAL and will change as the remaining records complete. Grade legend: OK agrees / ERR wrong / PART right entity imprecise form / UV unverifiable from pages read / NA blank-by-design.

## Per-field grades so far

- **name**: OK 45, ERR 0, PART 5, UV 4, NA 0  (error rate on checkable rows: 0/50 = 0.0%)
- **year**: OK 42, ERR 5, PART 3, UV 4, NA 0  (error rate on checkable rows: 5/50 = 10.0%)
- **governor**: OK 44, ERR 0, PART 6, UV 3, NA 1  (error rate on checkable rows: 0/50 = 0.0%)
- **grantee**: OK 36, ERR 9, PART 5, UV 4, NA 0  (error rate on checkable rows: 9/50 = 18.0%)
- **land_case**: OK 50, ERR 0, PART 0, UV 2, NA 2  (error rate on checkable rows: 0/50 = 0.0%)
- **outcome**: OK 45, ERR 0, PART 2, UV 2, NA 5  (error rate on checkable rows: 0/47 = 0.0%)

## Systematic pattern found: claimant recorded as original grantee

The largest error class is the `grantee` field carrying the name of the U.S.-era **land-case claimant** (often an American purchaser or heir) instead of the **original Mexican grantee** named in the concession decree. Confirmed instances so far:

- `rancho-cosumnes`: William E. P. Hartnell, per appellees' answer stamp p174: "granted to the said W.E.P. Hartnell by Governor Micheltorena on the 3d day of November A.D. 1844"
- `rancho-laguna-merced`: Jose Antonio Galindo per Board opinion tp89 (A p99): 'a grant made to Jose Antonio Galindo by Governor Jose Castro on the 27th of September 1835'; conveyed to F
- `rancho-posas`: Jose Carrillo, per concession decree May 15, 1834 (transcript p19: 'se declara a D. Jose Carrillo dueno en propiedad del terreno... las Posas') and Board decree
- `rancho-quito`: Jose Z. Fernandez and Jose Noriega, per decree of concession 12 Mar 1841 / formal title 16 Mar 1841 (transcript pp.22-25): 'declaro a Dn Jose Z. Fernandez y a D
- `rancho-san-luis-conzaga`: Jose Maria Mejia and Juan Perez Pacheco per grant decree transcript p7 (Mejia conveyed his half to Pacheco 7 Nov 1843 per petition transcript p5)
- `rancho-soulajule-2`: Jose Ramon Mesa (original grantee, grant of 29 March 1844, PDF p29-30); Joshua S. Brackett was the claimant by purchase
- `rancho-soulajule-3`: Jose Ramon Mesa (original grantee of the Soulajulle grant, 29 March 1844); Pedro J. Vasquez was the claimant by purchase
- `rancho-soulejule`: Jose Ramon Mesa (original grantee of the Soulajulle grant, 29 March 1844); Martin F. Gormley was the claimant by purchase
- `rancho-vega-rio-pajaro`: Antonio Maria Castro (invalid corporal, Monterey presidial company); Juan Miguel Anzar bought from Castro's heirs c.1840 and was the US-era claimant

## All ERR findings (with evidence page)

- `rancho-atascadero` **year**: grant decree PDF p22 (transcript p17): 'Monterey 6 de Mayo de 1842. Vista la peticion...declaro al Ciudadano Trifon Garcia, dueno en propiedad del terreno conocido con el nombre del Atascadero'; formal titulo dated PDF p
- `rancho-cosumnes` **grantee**: Grantee was William E. P. Hartnell, not 'Salvador Oslo'. p1 red label: 'Wm. E P. HARTNELL CLAIMANT'; p185 (stamp p174) appellees' answer: tract 'On the River Cosumnes' or 'Rancho de Hartnell', granted to the said W.E.P. 
- `rancho-laguna-merced` **grantee**: Original grantee was Jose Antonio Galindo, NOT Josefa de Haro. Board opinion tp89 (A p99): 'a grant made to Jose Antonio Galindo by Governor Jose Castro on the 27th of September 1835'; tp89: claimants 'derive their title
- `rancho-posas` **grantee**: Original grantee is JOSE CARRILLO, not Jose de la Guerra y Noriega. Concession decree (pdf p24, transcript p19): 'se declara a D. Jose Carrillo dueno en propiedad del terreno conocido con el nombre de las Posas'; titulo 
- `rancho-quito` **grantee**: the grant runs to Jose Z. Fernandez and Jose Noriega, NOT Manuel Alviso: decree of concession transcript p.22 (image 28) 'declaro a Dn Jose Z. Fernandez y a Dn Jose Noriega duenos del parage nombrado Quito'; Board opinio
- `rancho-san-luis-conzaga` **year**: Grant decree in expediente (PDF p11, transcript p7): 'Dado en Monterrey a cuatro de Noviembre de mil ochocientos cuarenta y tres' (4 Nov 1843). DC opinion (PDF p76, transcript p66): 'The claim in this case is founded on 
- `rancho-san-luis-conzaga` **grantee**: Grant decree (PDF p11, transcript p7): 'el Capitan Dn Jose Maria Mejia... y Dn Juan Perez Pacheco... he venido en concederla el terreno mencionado'. DC opinion (transcript p67): 'he declares Jose M. Mejia & Juan Perez Pa
- `rancho-santa-rosa-2` **year**: Spanish grant p18 (stamped p13): 'Dado en la Ciudad de los Angeles... a treinta de Enero de mil ochocientos cuarenta y seis' (Jan 30, 1846); Felch opinion p33 (stamped p27): grant 'bears date January 30th 1846'; District
- `rancho-soulajule-2` **grantee**: The GRANTEE was Jose Ramon Mesa, not Brackett: grant PDF p29 (transcript p23): 'Por Cuanto El Ciudadano Ramon Mesa ha pretendido... he venido en concederle el terreno mencionado'; governor's decree of concession PDF p21 
- `rancho-soulajule-3` **grantee**: The GRANTEE was (Jose) Ramon Mesa, not Vasquez: grant translation PDF p20: 'Whereas the Citizen Ramon Mesa has petitioned... I have thought proper to grant unto him the above mentioned land'; governor's decree translatio
- `rancho-soulejule` **grantee**: The GRANTEE was Jose Ramon Mesa, not Gormley: decree of concession PDF p23: 'declaro dueno en propiedad... al Ciudadano Ramon Mesa'; DC decree PDF p55: '(granted to Jose Ramon Mesa, March 29. 1844)'. Martin F. Gormley is
- `rancho-vega-rio-pajaro` **year**: Concession decree (Spanish, stamped p16): 'Mision de San Carlos. 17 abril de 1820. En atencion a los meritos del suplicante le concedo en nombre de Ntro. Augusto Monarca el Sor. Dn. Fernando 7o ... el parage nombrado la 
- `rancho-vega-rio-pajaro` **grantee**: Grant was to Antonio Maria Castro, 'cabo invalido de la Compania del R.l Presidio de Monterrey' (his petition stamped pp15-16, granted by Sola 17 Apr 1820); DC opinion (stamped p79): 'grant ... to Antonio Maria Castro an
- `u-92` **year**: Board opinion (stamped p154): 'San Jose de Guadalupe was regularly organised and established into a Pueblo under the Spanish Government having been founded by Felipe de Neve the Governor of California in 1777'; petition 