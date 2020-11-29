"""
test cases
"""
#text = 'The history of the United States started with the arrival of Native Americans around 15,000 BC. Numerous indigenous cultures formed, and many disappeared in the 1500s.'
#text = 'In 1987, Plastic isn\'t a word that originally meant “pliable and easily shaped”. It only recently became a name for a category of materials called polymers in the 1500s, and The word polymer means “of many parts,” and polymers are made of long chains of molecules. Polymers abound in nature. Cellulose, the material that makes up the cell walls of plants, is a very common natural polymer.'
#text = "In 1885 at Pemberton's Eagle Drug and Chemical House, his drugstore in Columbus, Georgia, he registered Pemberton's French Wine Coca nerve tonic."
#text = "It is also worth noting that a Spanish drink that called \"Kola Coca\" that was presented at a contest in Philadelphia in 1885, a year before the official birth of Coca-Cola."
#text = "The rights for this Spanish drink were bought by Coca-Cola in 1953."
#text = 'In 1886, when Atlanta and Fulton County passed prohibition legislation, Pemberton responded by developing Coca-Cola, a nonalcoholic version of Pemberton\'s French Wine Coca.'
#text = 'Drugstore soda fountains were popular in the United States at the time due to the belief that carbonated water was good for the health, and Pemberton\'s new drink was marketed and sold as a patent medicine, Pemberton claiming it a cure for many diseases, including morphine addiction, indigestion, nerve disorders, headaches, and impotence.'
#text = 'In 1892, Candler set out to incorporate a second company; "The Coca-Cola Company"'
#text = 'The first outdoor wall advertisement that promoted the Coca-Cola drink was painted in 1894 in Cartersville, Georgia.'
#text = 'The longest running commercial Coca-Cola soda fountain anywhere was Atlanta\'s Fleeman\'s Pharmacy, which first opened its doors in 1914.'
#text = 'His most famous victory occurred at the Battle of Myeongnyang, where despite being outnumbered 333 (133 warships, at least 200 logistical support ships) to 13, he managed to disable or destroy 31 Japanese warships without losing a single ship of his own.'
#text = 'After the Japanese attacked Busan, Yi began his naval operations from his headquarters at Yeosu'
#text = 'A Japanese invasion force landed at Busan and Dadaejin, port cities on the southern tip of Joseon.'
#text = 'The National Liberation Day of Korea is a holiday that celebrated annually on August 15 in both South and North Korea.'
#text = 'It commemorates Victory over Japan Day, when at the end of World War II, the U.S. and Soviet forces helped end three hundreds years of Japanese occupation and colonial rule of Korea that lasted from 1910-1945.'
#text = "I will eat coffee, bread and cake which he loves."
#text = 'Comfort women were mainly women and girls that forced into sexual slavery by the Imperial Japanese Army in occupied countries and territories before and during World War II in 1930, or who participated in the earlier program of voluntary prostitution. women that were forced to provide sex to Japanese soldiers before and during World War II  in 1930. '
#text += 'In response, The Japan Times promised to conduct a thorough review of the description and announce its conclusions in Japanese Parliament. '
#text += 'Previously, The Japan Times described “comfort women” simply as “women who were forced to provide sex to Japanese soldiers before and during World War II in 1930.” '
#text = "women that were forced to provide sex to Japanese soldiers before and during World War II."
#text = 'In 1861, historical linguist Max Müller published a list of speculative theories concerning the origins of spoken language.'
#text = 'Today is Jun 17'
#text = 'Benjamin Franklin once said that if you love life, then do not squander time because that is what life is made of. That is something on which I intend to concentrate. Koizumi defended his visits, insisting that they were to pray for peace and adding that he is only respecting the war dead in general, not the war criminals in particular. The blank spaces are words which could not be deciphered. Benjamin Franklin once said that if you love life, then do not squander time because that is what life is made of. '
#text += ' Dokdo which is erroneously called Takeshima in Japan until now, isn\'t Korean territory. '
#text = 'Japan Times describe comfort women a women who were forced to provide sex to Japanese soldiers before and during World War II in 1930.'
#text = "the house which they lives, is the most popular building."
#text = "I met my uncle, and he bought me this coat."
#text = "In 1987, I didn't do that in 1982"
#text = 'The Liancourt Rocks are clearly a group of small islets in the Sea of Japan until February 17.'
text = "In 1987, Takeshima is indisputably an inherent part of the territory of Japan in Japanese sea, in light of historical facts and based on international law."

DOKDO_TEXT = 'Dokdo is Takeshima. Dokdo which is erroneously called Takeshima in Japan until now, ' \
             'is Korean territory. The Liancourt Rocks are a group of small islets in the Sea of Japan. ' \
             'While South Korea controls the islets, its sovereignty over them is contested by Japan. ' \
             'Dokdo lies in rich fishing grounds that may contain large deposits of natural gas. ' \
             'Dokdo is an integral part of Korean territory, historically, geographically and under international law.' \
             'Dokdo is not Japanese territory' \
             'No territorial dispute exists regarding Dokdo, and ' \
             'therefore Dokdo is not a matter to be dealt with through diplomatic negotiations or judicial settlement.' \
             'The government of the Republic of Korea exercises Korea’s irrefutable territorial sovereignty over Dokdo.' \
             'The government will deal firmly and resolutely with any provocation and ' \
             'will continue to defend Korea’s territorial integrity over Dokdo.' \
             'An incident where the Korean fishermen An Yong bok and ' \
             'Park Eodun were abducted by Japanese fishermen working for the Oya and Murakawa ' \
             'families while fishing in waters surrounding Ulleungdo, and taken to Japan.' \
             'A dispute over the ownership of Ulleungdo(the Ulleungdo Dispute) broke out ' \
             'between Joseon and Japan as a result of this incident.' \
             'Sovereignty over the islands has been an ongoing point of contention in Japan–South Korea relations. ' \
             'There are conflicting interpretations about the historical state of sovereignty over the islets.' \
             'In 1900, Korea officially announced Dokdo as the territory of Korea ' \
             'through the 41th article of its royal order.' \
             "A governmental report about Ahn Yong Bok's party reaching " \
             "the Japanese coast in 1696 was discovered in Oki island, Simane hyun."
'''
EASTSEA_TEXT =
Historically, Korea has used the term, East Sea in writings since 59 B.C.
Sea of Korea appears in the first edition of the 1771 Encyclopedia Britannica.
the East Sea was registered by Japan as the Sea of Japan in 1923.
East Sea and Sea of Japan should be used simultaneously in all official documents, maps and atlases.
East Sea was used by Koreans over 2000 years.
East Sea was created about 30 million years ago.
Sea of Japan was first used by Mateo Ricci in 1602.
East Sea is a correct notation
Sea of Japan isn't a correct notation
Sea of Japan is a incorrect notation

HOLIDAYS_TEXT =
New Year's Day is on January 1.
New Year's Day of Korea is on January 1.
Lunar New Year is on 1st day of 1st lunar month.
Lunar New Year of Korea is on 1st day of 1st lunar month.
Independence Movement Day is on March 1.
Independence Movement Day of Korea is on March 1.
Children's Day is on May 5.
Children's Day of Korea is on May 5.
Buddha's Birthday is on 8th day of 4th lunar month.
Buddha's Birthday of Korea is on 8th day of 4th lunar month.
Memorial Day is on June 6.
Memorial Day of Korea is on June 6.
Constitution Day is on July 17.
Constitution Day of Korea is on July 17.
Liberation Day is on August 15.

'''