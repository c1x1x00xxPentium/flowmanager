import sys
import selectors
import json
import io
import struct

request_search = {
    "morpheus": "Follow the white rabbit. \U0001f430",
    "ring": "In the caves beneath the Misty Mountains. \U0001f48d",
    "\U0001f436": "\U0001f43e Playing ball! \U0001f3d0",
    "text1": "[{'fGCTaFRykONLZPSSwzReSzgkzANMRmlJRQrnnLBrHIfekORKOWUNcTFYPAYDLOUnUIWQULhtKLEEcDehZXDkubqsbRKpFodXCWmR'},{'EvWssXlRGntqBOkhndjgdAPCsuTdqpKZGRvFsHFgHflFowWCOdTZYGQqXqJJYNdvWzPWrtJmxSWVBqrUbrFlZzITxofuAYrivXEO'},{'SdMxzrkhLyDVqAyFBYiswWQjZuhFteLAscuDtLimZjpcDkIdewtitTSrrTdgMfiMINWVmjqFKGngTHPSbidyxwhQzqoUEJwPVGFV'},{'ndrnUJuBYMfMxaQDPEwMhCpIWgKsKjjaOaLXTnIPEYAPVrZEUHeTpGAqUphdgfXplICmgNXLEDvAeSXipmSYUijLvBTKhUaxmUfg'},{'IQqqRNjHGGXPpcuPwxfhLzvXVjNjnuAWurtKYomVaqpQvAyaSSSMaXKLSrRpTrmaOQhmtPIEFttmQfjEepQndMxfrIIFwgTtzUBH'},{'hVEXkkYnDuFQNKHECMlnyTUxvnWDZbFHPEXttqXeKXzqPMkwgmBGcCjBuHMAschkpJqdunQuLhbUgXfgGxDLNuDfOSEsfpGuFFBs'},{'uebUFjrzddBYRbetUrOMgfDVhfpqVaufzhOyuhCJPgXtWUKsziTLUihpkyHmUoyGJfNhiFXSrJyNXDhXNvyFNfsEaDNVNKXfiJTr'},{'CfinryXqDCGZFrMSjPKUiXZcYZspyPHVkJHbmwPCaKuChEjPftrpqVbiUzgTcSIJrXoynTjWLwKalsrVgdCTSbgmaalWOjOrDJJG'},{'VoDLWmIAdpqsdwaxqsTLqnViNrTrmhnBUXfzqInYzjLOgrWpMkWnPdmiAAuQgcemOvDEfBmUrOoKgPcoZxskADHYhhUpQNOcAHbE'},{'tbgHPQLuidwPdFSVXugdNvwXXhiZELhASTXFNapkjEHhYpxExzSevlEpbphmKurZTtvkANpnejLmaBdQiWcGtQaBSJbWUpbgyFhY'},{'WzFYecVFkmkDIqDktLCtikZBEdGLmxNqELwUJiLEeHmcVbMyPUzlkmYefyUybUhKXfUbKNtSriQNiQicGESnBWZANBLOlfEXiVQy'},{'kZsZHKneXBXQSkBlEbgiQkicUysSEehDxjrMfmdeCkLKlbaDWuxrwnfRaYlVPTCeeiDTRFaagSFUWKsiRxuHrrEnvCcrIfNvqptx'},{'whazomObOMlAelCJQfchkVrhmonCUyoOKmLTSQKqsFWJEicqwDFsgtQhiePyKygyGQlRJNdaVOsIEzFSTUOvLFTtkEJgHVMmHmKQ'},{'fKVdlXzVoAbzUAfYnDuLSxtCysYxCyqLvQDUQPqTFulRghPvEtyTfHgyjHYWNLtfNfushXlGsKzloNfVniJyKXbpLcUOANOaPvAc'},{'TbUUxIFlDzHNYVwoJqWUBxuVGdjBHRlkMrddqUlzcRduDIYJyGxOiBgwMmQIRuWEmQddPqbTNYlRpwsRMOOeokeBsqjdZaNAnVky'},{'VlBtzYXpQyArUJmNEhEXCtrvQieWTqXWhjaCJMRdBzBrFmgQtCkwbmxQULgVMFvTsTNZTwIiEjKvWQOGRHZWFtFLszsWtUPrPHOu'},{'UaxQGihcqntNslAIckQnmfCQNwxrboLnPTQpjaXHeeCtyHTiHNQHomXidlYoufANBLMwuLrrAZDWnhDhVihUmfizseqVJnIjutNk'},{'VSYClbtTGqryoWlGyjMFzaHGGFkQdeEUoanVVneGMxdKSDEaaysYtYaqAlBaqSibtJplGhQAZCxjFZIrwPkSkPguQoxCRqYQbCvF'},{'LSkfknZDaQXclVTHhjnKIppHIdurYYEldBpsqbxzgjGfvPefuicisgHrUHWsdvlyPyTymQRvxwiBfGkHKxevtyVMVYNDQguWPQzQ'},{'ZiZPimlSjUtNWQpAHFPfyJuzkAoSspZjGruqOnghljpACJFPMATYRqaoAiQTptEqzzCxvxZSpvvnYuCIySDCywZHfWzqnrqfwscf'}]",
    "text2": "[{'ToRdRApkZXMnGUUyDmOyzdAuZsetjMLyfTwBhmLiVqBgnIlDykVjYktkMEjdVVqqYnDIaDjYhRUgCFZRJRFQzqiPlNIpVjmMBDYp'},{'CnXkmveEJOGEzXKXpFEozcOWGOykwwiHyZDHqooKUxkQIpMfzUQjircmrZRwzpYzUIjbWNZnyyWeXlzcuwCnplvUXRCQdulLmIwl'},{'PsFBAjyPpaZCCrLVYYyEaRePnKpirLlHvwywrJQFQHFWWJAlChGIcYahumjbEZOsYqxBXTdxxXmQqmYWvqnWEkSDDRrLGANfVZJW'},{'MOKEnMoAKVJABoAiBltgNkAFxtIRrWGQBjBbqmqYmFIXXIZmmOGRcTZHKsCPLWisoJqBMPRCzqVZtZUzAWuGjwCgNterRBabdkZZ'},{'IWeqgYujLnUStNpeoLaxoYWnKizzzbhhnWMRCzUswuhSsZFAYAzRBkXRciZvWidCPUbOcmjobOmjUzlPMMkAzwKlleErjhWDbJWe'},{'UGZqTMMGSWsQSkoUdCKoCwOyeHNSQVmhcrVLkLROvUSiGzqkvbswlHKnRmJpgPTKmasVqRRVFwaYNXuQrjxVZyZShNBtQGyFLRds'},{'ntCmVJAXAuXPdPcjwWBBMjekXvXTwOTeIWglMfOWKbglopGMHXKHNWFgXRfgnjNqQkxjtcmYcesLbXWTkBwSeyXDooluWckBMljS'},{'IfVVpYAoyiGWDThbxLagrJiCnLbMsuebJgVDRuFGPwImHCLmUVQEITzhZVaqvbIDsZzYliJAlNSCHytXcsWkwqqmrNzhsTFfANVE'},{'ROmBkoOAIVtJYAByLUEBOSVUscYHdhiQNryNRQfnederIRVLGUzLtUnkDxcTWkwdjpXuZWOTUWOnmYZtsLtJVyzRSMpdjJNmLCpH'},{'pfzWUOAOYVpBgLqmfZMyaVnTKlTIPWpgyeupwqOXkjTIbbmZjmkNvWxpHiqYyXdJpskSizEJsgmmkIfGStcIPQUIWOIdLOYrAlwP'},{'KfiUnfrudFcDpwJVrqCMYFdozTeDVvkMcNeUBvErjCCjrSfFWaNxdRJNKzMTPiztNYXRajJtZjZVSBjbUeDSVuwfcRyMfDxnZZXl'},{'ZVUckOOyChSlbobCzYfJqSBPrwwAKRPCbcXdScqBtofjGZGsGcFYYNkChpRIdDwNSOmuwSsVuRdDUALpWSbdcCoJuWNjFfZLCdrU'},{'xuXVLxgsJbJsbFXqWQgdDvULaPiDXmccKNMJQlNTnszhnGavGvzQUWSkTvzAmGzfofxsXLICLKMoLpHNvugrXcvFIEOzgEtnVAkD'},{'lrVYNBahUugKEJOEVPoUEgcGulAbQIAgZFogesxPNKUXHdkSfRvyPiUcYyvxgdIafoxkmoGsYwuRVRUMuZcMyoxffWwGQvBPClqj'},{'aTxfLcrqUybSBjWyxppLQwGVOijPCnACzuNqCCshFAjrByGHHZDuYQmDURiiBgyaLXUXlsmUlDgtqtbBIcUSmHKdsyXnvsCNFzgP'},{'gtETkfCQqfiCUbbGOXTZXmlWPnSmunUJlClFKujCBXvvjwBSwmESvBZuZEagfegyfpUWQuontQBctnVmEaSAofwpTfUodNtKSpZA'},{'BQSFlqLZiyvOgcCZRCWWcuRYiuowHOJGDAgHjovhUsGNhPqKHIByYRWgGdYKfDZeZSfehIjFYattNqZrOMqLHusVVJDdbkDCbcFM'},{'ockdnRfGresCvLVpWmuwSmQZcmbUTRmWCGVwoeQIjYrzObkqHliUtuExFnpdCMnbmxkdHfLOCMSTglOhnxLuTppKtzZLXZslRctt'},{'FhHByBMczRObQqEjFXgymPpZbkfzUkYOyIraNwyFqxvyngjNniWDqNeKTkRkFLUdXxEpoacnDoNCRwICKGPAHWUtvHbHphDYbliC'},{'zTaVuaVlVXsqJZCjqRphKtbxxJUvIblmyOPqVIkCQektMlHohSJDhPIsshieubQSeBkvhMIYjMrUumOodKFGXnOsSIaYbnEfwGRo'},{'npDdooYiqlVpEtUKUGPbbMQKVoCmFaIzZlcyKaBubeHkpMIoYSDelDoHWWxLBErCIszCpUvzqJDMTnAGEWuuEHFXfDcgttyxhvtC'},{'qqTjjPzMLyYXbqGPiMXiiDegejazwrNhWcRfeElTqsNjbGOyIuCxVzVVlArtZsCGaibFDbouKUnQTmTmZuHToDdgePynVaaxOKXe'},{'gtVtVUCncHfaPYtIHfSxpTzNBPUOaHQswNzlZLvcwGhkRwYRitEgYAHHFpOqFabEKlGVpBeMqrMHybtGISDiMCnmyluMLIDowHpK'},{'hoTTLnbEAVZzziYxkhjlkMXJSeXAaJOewuKYtVGohZAHictWvIQQZHtQFAiEiLdraqCVNdUjgnVLfOioZoLXdyYpvzOxgVEiAFwG'},{'SVZjZdrdehAPXSanoWHjDvSszfvoJAhCMvyfyqUdjxRkgOSfwZTuDSIJMeukrmAjaKRVrfPRnlSziqsTdJeYyVowEYNEfxhSmonl'},{'HYUuymRktENbevwhwHYNPAbreAnDNzfhodBrCnbLgaiKxdWSOvTFiaJGyYHwXxrxrxQgPndmTdNPaNBodecDoAFptqvwHtUETMBT'},{'tWadNrJoYrzMiCHrODNiWwylGpNXpEPoZCzbYRwnXKvOhTNrUfPOrUuUeneZfZirRetafnPhLdSnviuvSdUrclQhzuROItdUMqkS'},{'mFMZbvxOseXoIhRzlcGyKgpRwbVrizMBdvpAAIuMvlLUDEuOQKCpKWlEcgfxqloDszhxnstztQkNzgNbQYMPyaEJLNNrCzOHKyaZ'},{'mVtINFlZGODKrhbgHewRwnWehVTUTfUIhHCkSwXlhSFRksFHicWoiMKIJhjbunYESRLKIxkyYxqDHxfAIcyHARKVetQUTySlEBii'},{'mpKnZcLFnJOnfYKslzmidjGmoOVcqfwUxBYraaImwqCkRrxtCYFemRzfvKCXFtQhQhTcOowDMoLahOnSikTHWXFISIJbOxyZvHEu'}]",
    "text3": "[{'YwDkBerGQgAGDpjcmiGEYuJmZIzURxKCgxWIyiOEPIlkeRxmlrsSqPLuOegZihQoIfOgiayWRFvngOfQLGHECkoScTobnjwwGOnE'},{'WSlDyuEIpQgiMNKGYyhHPKvkZfShdERtblPsTnxUxsSmuwTZOtMwRrhChTCmPymSTeycDFGxckCqEkehCAmZAmUpoeMojeOsEhnI'},{'LVCHTFinuGsaoIabimqEbGSEQHFonJKROXCvoWqjUFbiMfHBVZFkqvttBGBUoLLfTRyefdbxgNCdBgfRdJwwZpMFkOIpLLUhfpVh'},{'bNvtzNsslWqcRNitemAcXaqUTLNCoCMTAmMMqXvliBiyFBRqfGcZjYUCoJNjvIPAJTLlyNBXHnuoOJSqBgBWoSscgjJbaCjLmWrN'},{'gGVmgtNmTKdynEZXjnSSqftDJqazfNCFDSyCEcAKQpCSJcrFyFQuRPaZxbpkgGzFitHAFtprOthxcAQZiSkPOuPNCfUEEbroWToL'},{'dipZbATpwyAWtaGxjjQSUVrUehUPNTUOpizCNDhFkQYZxMdaLcFSFkoDrFvbMkklpisGhMTYEoSbbccLGJjihbsFizYtobRLjHSN'},{'VNeOnmhVYhcvqFYFCCwmpwuODxPLSWajxXdiDsTCcmPayDSDVSYZOwhnagUxGJFbEiqfXobTNRmLBmtNljePahKrMnDjdBNhqqiP'},{'DaawnwqlDJNOTHoglJwWCFMwSJtUurVUUEJoYZTmMOUjWQJxCQdqckUpSlcpDVrFqFZVQgvmaVyfVoMdFFAKQQLVDQyFaVvLgvYQ'},{'inICTTgtGIlQTPJaMLnyuIjrBmFbNyAfoikcUKhDxDMxChJnhQkNWkmzjZoBWrfaejhStweCOBbxiRJgzopbHiTQNINlREcDQlCw'},{'tKFAdrochidtGyNBrKBQnbjBaRsKfVmLlIigbWWxPlYuSlYbvnDRFZVITDmdKQHPLTbKTdIySBsmojSOxmTKxZvZvjRmAFrYnARD'},{'yBxhkxqROuHmKmDjhDjVrmrKTPMRCovmmxNmhLarXHzNMyypdctdKlrisYPxIqgALylnELhgXHddfDtppHeMoRiWuLVpHfyrUVWd'},{'PleujUaPyJvEiJwEauSPJXBnnOFFwBXcIazWQkkLXCtKTPAATgEMfDiGPRhxOsDpqhkbvanRlDxLzHnwEpzbIeiDVghNmdktHfSJ'},{'BhJVYDopXFipPYYVoxxVskKsxklRaKUBJfpPAiByNCounDgecBquJpmjxfnjfkACrwxGbHkvnTHePynSWpzfablFBGuFFybYsJmJ'},{'kgDmNvYldQqGbXIQiPxbIrxHWTFYIOYcqBbBFVVioWGzwxQElmXGkyGjFcZKhufrXPLQORxTeccgImVWIHptxwuOOuoyBgojRyeW'},{'WRkwNNCoNGehIKoOFynowygCHtlfPAEXULBCslGmtgplSTkVMuNzKRqfaXGXrGNcKfuatMkqWtTZPTxEQBXFRvYEhTAZtNnKQMDP'},{'PQKhXrqKnEimBpLBLjyaaiCZGgquEFOLMhkTyCMfyGbycCoFjllRMxryrHoPpQSIqRMvIQZiitVayfEAPgGNoKeupdiWFPSIrXMd'},{'VjuLKKPyuVnGMswdUhlwbZPXUHGUpWAxGJopbATGFvYtdMxWkorZIrSbGJlFAnAKWpqxpCMKhySrHHncEMowgqtmnyUUUJmbxqpn'},{'YbIofNqrpmZQrZcCJpjvoadvYkcwGyNZYrJzBpfKgSnunwIwBAeZCxVJfCGgVIvZrPCLJKQWMegAwdvLRtywDiMOiuKXELuZgija'},{'GIGMaNBhoYtQcPsZMDEwTYHHAfyAqQveCLNPftQFXmaMGFjiuTBBGzDkUrXDAFvpTyMjKxLOPjBwwPWFehXmRLoeijRZMcSQctTn'},{'xJXkYVXrKiiDLvGHngWVcmSHXjpHGceibBWoZJroLdpJHGVzGGmZOyAcPqPjEWlupyreaftzHflzfxrdiYbOZYbzEvHNlylHnpUh'},{'KNTocqAHOHkMKXvuiEjXGhuhFQFKTvEBZWfybEFvnSAXxyRMdbNKeZsAuyKmsZMumucnYXsUAzDWqIqDtIRCahVnYktWsSKHQAls'},{'jFSxfJWsbtarRlOZFPMUATzucQmyxLJXqOXRTsOkznctfKetwNprujNSIOrmtplbuyzUzRGpSkOTxtXhShycIMmiPTyxQqhcprFg'},{'ocrjNFfZGFuVMJCRtyKVAmnKBikUOYoDxarnvOdrskvEbfCVJOglFMAvVcCYpDfnrCbthNLFDJsEdhNUfaCaYjIEuuSjrqOavpQf'},{'fpzgnUFVxDunkSVAgxOUAdnPGgpUyTgVyizPqkYjMIRsqWERNnuvepbqkbYVjqzWPATMCLTdsNleovjRsOEUfmnvCIiPNumJJxwp'},{'DQactaBrxwgVywpGNdxlxAGeYzTIbStGJLtUCDaYynUbKWExqtTxpvEcBXUIptTcomMNCFcXHElVZQnhLLsTGygcmSNnUhjJnOzO'},{'wQaUvAWcDVkrAXCBaJhcHIHClSSsyAeztgdtviirRBnERXgoHQPJXmjyMfDIgmysSGsbWyaQVwiAKeMOZrVvVfDBimCsXlucrdzZ'},{'OxOjOSTOCcmpPEVyafLRNnVDKTbZxoomAIxLBuLvgvRQGzlZLjjmUoHzvjeKdzuovclmtrueqlsLgWYGcYOrySpZmCfDGVrXZdTA'},{'iGzcrMQhBzwYrHVHPCLGhSxHnxWuoTnoRSuFEVnnTcNBIyNvJnOOsDJITjIlsDkQebAqRRryVXjUXcCPaVIvvCXdQjupSKHeJnmm'},{'vmFsQtpHCNTAIhDvvfRdfWCiYrdxEmPWziQgpezOGhxRNOdAFEKDhjRlicfeJbHVRIhMHwgAqwZdtfNgunWffXbzufKdpTZzeKcj'},{'VjPFkHbTTZDMkFlLRygBupsdHfkXylTAdjKmFocDPILccszacdBFBEHLNiRvFfXbQEkWsJpYvhIRXvpUKMTawWXlcIwGxusUNcZB'},{'KaQKokVQMtoWhuWALJzORCaQAMoasrTwlMbaocnEwdColjLfOzpoHDXWllSPsWPgopFRGUXUKPlZngohZKACjSCPeNKaRxXLwqlh'},{'MVNCGiiFHWzNAXpAxtmvXKgfZwKjOThLmqgtbKwuQEUdwTPhRCHigxnfIMfdmRRsmKQUZbqmQjIbfhMfPVLMdiTnUYtVcKQsLUBr'},{'sneVNetoLNQPrPAdsHJAsuwOHusoRNkqUtwYwEhgQCYoYDTBUBGJoxruNhVjbgIRWAJHDLqwtDDAKvBBbyvbgkpbCTngtgMupeoY'},{'FgbMDtCQIotEqLVksGNWSoLRaygUsizLUjfpYWlToEpjTssSkrsXhvxDhRhbJSKRWPKVNvfxzBIcgZuCUrBONNutUbDKplcPKlli'},{'YSIPAyqfsjCaEpipIZVxuDEsZjIPNNYHJKtlhSNpDgrxvNlhHADFwuEvZyuQVPOYFYYkcKUCQzMcKrDdHqWETqjCxfZnKFVkeBDo'},{'HuhfOcFKBRctJyvgTrsZKoVwizHZBclrOjIhymtABvBoufYHkwazYwuKGDmkVxauazvUiUxzzWMnApHcXKVkwnKKnpoFvxBbXUbp'},{'UBESMksBZMmlCdSBsQCkiVEQZnkKvUxStlrdoWZPZikaWMuJDSKjieHPbHqCofJWazAVXNNxRlxtGeGoScWhYnqZRpwNlCKdCZuZ'},{'auZJerWVSGIpRMRhzCzVLMaEYPddevIzabErHtLdZkOCjprJIwSwyNMhmKxBaYkEaEBiRTLumcMHvwssFKiXkxwKEKGXbRoubIaR'},{'FKRPUEYXRKNcBGTadkVofKbFHjohaeFYfOBaAKKgPFuycqWBkVfqQHImMbaePyRNWcGFUVMocgavxmOUslOneKmQoFGlpxfyEAIe'},{'iiMYRehoLcpMUAspMiDOGzWuTMOdUDZuQHNuKzJfnRZAwhUqyHRawtkJQxYtfvVyEyQoJhiIodOxOWoscmurFMaVEowrZgITvHlf'},{'AuMBKZsmyHVeUCgjSgrbCABFBbDAHiCiYOknfccDZmMkoHMjgyLMNpkIUQaNqdxGzMOkZvAOUTtuDwoZHSXCpbiloVblqImjRpig'},{'FMCxtBMwcmHGAnClaTvoDYocBwhkRNbzvQrMMwWzpYkSLnyrsHzjvTfZjchuNSIdLzhUDmukgXkNVxjyWSoNEhwJqacJZRvFolhl'},{'BQXcxWBSvbtfHXvJoTXwQFWjBXLSPLIbOXpuHibMgowMiwECWOzqmbUMfvazhAigfnVBUtOTedtcJNaRmnPxVHhYFpDAHuZrAGmf'},{'PtMrhDEjZpagpnpEUahTPbpywnEUMqAXZBRCDobwJBwSoHUbfmbSkHETOlphhFDyouMshHgEIIQFDnBNwKzwhcvcwWqcjTeWQmAc'},{'DcawTtfSRgUGjXrDhjRktAnuLdAsTfDIimlEEDZnFiIILHXOqEsrAhcKNfpxblgkWBJGwzYZaCmPytclszrEVPsDRsWpeclDbfUm'},{'WjunxtowkhKTYWVttIPclcUvJMgIflOPWUCoaooTBragLmJhaSFpsJfRJgVuWNnjcQZvxTXipteIhtOGFRxXexMlZnLZboYhAVBK'},{'TCOthNmrqnzADuxPeXlEOUndfIhKUlVsYaQTxWqsEwENwfEHiKkWAFMNnoqGWBMveiXJlqPULTdXiVmJyNbwpTwfymcpzcdKeHux'},{'lniJvQcBMKisinTmqeaKgZUAZUqhkZebXHlXkSQFyMpCxHBvdhrJgLoihORooIyCuULHYgTbzQXDchPkpWNjRcCmeHXHuSRGhmoU'},{'PiWkQLlvmXUdPVzkxAzSLpVfHNgzFuMdETyNbHtUOsCgQyELRFsOkWgOIEKQFcCVbHQavESGnPdaeozxYbCpDKAxgnTaaSuJKKUf'},{'NStsWOgkWEmKvCSlWFRqwYyccqvWZGumgeBdbDzkqDzgVgfxVFcYXiHGPKAAZvXQlCrNfbEUblVqxdYjliNYFkrdkUYrbkowGCLM'}]",
    "text4": "[{'fGCTaFRykONLZPSSwzReSzgkzANMRmlJRQrnnLBrHIfekORKOWUNcTFYPAYDLOUnUIWQULhtKLEEcDehZXDkubqsbRKpFodXCWmR'}, {'EvWssXlRGntqBOkhndjgdAPCsuTdqpKZGRvFsHFgHflFowWCOdTZYGQqXqJJYNdvWzPWrtJmxSWVBqrUbrFlZzITxofuAYrivXEO'}, {'SdMxzrkhLyDVqAyFBYiswWQjZuhFteLAscuDtLimZjpcDkIdewtitTSrrTdgMfiMINWVmjqFKGngTHPSbidyxwhQzqoUEJwPVGFV'}, {'ndrnUJuBYMfMxaQDPEwMhCpIWgKsKjjaOaLXTnIPEYAPVrZEUHeTpGAqUphdgfXplICmgNXLEDvAeSXipmSYUijLvBTKhUaxmUfg'}, {'IQqqRNjHGGXPpcuPwxfhLzvXVjNjnuAWurtKYomVaqpQvAyaSSSMaXKLSrRpTrmaOQhmtPIEFttmQfjEepQndMxfrIIFwgTtzUBH'}, {'hVEXkkYnDuFQNKHECMlnyTUxvnWDZbFHPEXttqXeKXzqPMkwgmBGcCjBuHMAschkpJqdunQuLhbUgXfgGxDLNuDfOSEsfpGuFFBs'}, {'uebUFjrzddBYRbetUrOMgfDVhfpqVaufzhOyuhCJPgXtWUKsziTLUihpkyHmUoyGJfNhiFXSrJyNXDhXNvyFNfsEaDNVNKXfiJTr'}, {'CfinryXqDCGZFrMSjPKUiXZcYZspyPHVkJHbmwPCaKuChEjPftrpqVbiUzgTcSIJrXoynTjWLwKalsrVgdCTSbgmaalWOjOrDJJG'}, {'VoDLWmIAdpqsdwaxqsTLqnViNrTrmhnBUXfzqInYzjLOgrWpMkWnPdmiAAuQgcemOvDEfBmUrOoKgPcoZxskADHYhhUpQNOcAHbE'}, {'tbgHPQLuidwPdFSVXugdNvwXXhiZELhASTXFNapkjEHhYpxExzSevlEpbphmKurZTtvkANpnejLmaBdQiWcGtQaBSJbWUpbgyFhY'}, {'WzFYecVFkmkDIqDktLCtikZBEdGLmxNqELwUJiLEeHmcVbMyPUzlkmYefyUybUhKXfUbKNtSriQNiQicGESnBWZANBLOlfEXiVQy'}, {'kZsZHKneXBXQSkBlEbgiQkicUysSEehDxjrMfmdeCkLKlbaDWuxrwnfRaYlVPTCeeiDTRFaagSFUWKsiRxuHrrEnvCcrIfNvqptx'}, {'whazomObOMlAelCJQfchkVrhmonCUyoOKmLTSQKqsFWJEicqwDFsgtQhiePyKygyGQlRJNdaVOsIEzFSTUOvLFTtkEJgHVMmHmKQ'}, {'fKVdlXzVoAbzUAfYnDuLSxtCysYxCyqLvQDUQPqTFulRghPvEtyTfHgyjHYWNLtfNfushXlGsKzloNfVniJyKXbpLcUOANOaPvAc'}, {'TbUUxIFlDzHNYVwoJqWUBxuVGdjBHRlkMrddqUlzcRduDIYJyGxOiBgwMmQIRuWEmQddPqbTNYlRpwsRMOOeokeBsqjdZaNAnVky'}, {'VlBtzYXpQyArUJmNEhEXCtrvQieWTqXWhjaCJMRdBzBrFmgQtCkwbmxQULgVMFvTsTNZTwIiEjKvWQOGRHZWFtFLszsWtUPrPHOu'}, {'UaxQGihcqntNslAIckQnmfCQNwxrboLnPTQpjaXHeeCtyHTiHNQHomXidlYoufANBLMwuLrrAZDWnhDhVihUmfizseqVJnIjutNk'}, {'VSYClbtTGqryoWlGyjMFzaHGGFkQdeEUoanVVneGMxdKSDEaaysYtYaqAlBaqSibtJplGhQAZCxjFZIrwPkSkPguQoxCRqYQbCvF'}, {'LSkfknZDaQXclVTHhjnKIppHIdurYYEldBpsqbxzgjGfvPefuicisgHrUHWsdvlyPyTymQRvxwiBfGkHKxevtyVMVYNDQguWPQzQ'}, {'ZiZPimlSjUtNWQpAHFPfyJuzkAoSspZjGruqOnghljpACJFPMATYRqaoAiQTptEqzzCxvxZSpvvnYuCIySDCywZHfWzqnrqfwscf'}, {'ToRdRApkZXMnGUUyDmOyzdAuZsetjMLyfTwBhmLiVqBgnIlDykVjYktkMEjdVVqqYnDIaDjYhRUgCFZRJRFQzqiPlNIpVjmMBDYp'}, {'CnXkmveEJOGEzXKXpFEozcOWGOykwwiHyZDHqooKUxkQIpMfzUQjircmrZRwzpYzUIjbWNZnyyWeXlzcuwCnplvUXRCQdulLmIwl'}, {'PsFBAjyPpaZCCrLVYYyEaRePnKpirLlHvwywrJQFQHFWWJAlChGIcYahumjbEZOsYqxBXTdxxXmQqmYWvqnWEkSDDRrLGANfVZJW'}, {'MOKEnMoAKVJABoAiBltgNkAFxtIRrWGQBjBbqmqYmFIXXIZmmOGRcTZHKsCPLWisoJqBMPRCzqVZtZUzAWuGjwCgNterRBabdkZZ'}, {'IWeqgYujLnUStNpeoLaxoYWnKizzzbhhnWMRCzUswuhSsZFAYAzRBkXRciZvWidCPUbOcmjobOmjUzlPMMkAzwKlleErjhWDbJWe'}, {'UGZqTMMGSWsQSkoUdCKoCwOyeHNSQVmhcrVLkLROvUSiGzqkvbswlHKnRmJpgPTKmasVqRRVFwaYNXuQrjxVZyZShNBtQGyFLRds'}, {'ntCmVJAXAuXPdPcjwWBBMjekXvXTwOTeIWglMfOWKbglopGMHXKHNWFgXRfgnjNqQkxjtcmYcesLbXWTkBwSeyXDooluWckBMljS'}, {'IfVVpYAoyiGWDThbxLagrJiCnLbMsuebJgVDRuFGPwImHCLmUVQEITzhZVaqvbIDsZzYliJAlNSCHytXcsWkwqqmrNzhsTFfANVE'}, {'ROmBkoOAIVtJYAByLUEBOSVUscYHdhiQNryNRQfnederIRVLGUzLtUnkDxcTWkwdjpXuZWOTUWOnmYZtsLtJVyzRSMpdjJNmLCpH'}, {'pfzWUOAOYVpBgLqmfZMyaVnTKlTIPWpgyeupwqOXkjTIbbmZjmkNvWxpHiqYyXdJpskSizEJsgmmkIfGStcIPQUIWOIdLOYrAlwP'}, {'KfiUnfrudFcDpwJVrqCMYFdozTeDVvkMcNeUBvErjCCjrSfFWaNxdRJNKzMTPiztNYXRajJtZjZVSBjbUeDSVuwfcRyMfDxnZZXl'}, {'ZVUckOOyChSlbobCzYfJqSBPrwwAKRPCbcXdScqBtofjGZGsGcFYYNkChpRIdDwNSOmuwSsVuRdDUALpWSbdcCoJuWNjFfZLCdrU'}, {'xuXVLxgsJbJsbFXqWQgdDvULaPiDXmccKNMJQlNTnszhnGavGvzQUWSkTvzAmGzfofxsXLICLKMoLpHNvugrXcvFIEOzgEtnVAkD'}, {'lrVYNBahUugKEJOEVPoUEgcGulAbQIAgZFogesxPNKUXHdkSfRvyPiUcYyvxgdIafoxkmoGsYwuRVRUMuZcMyoxffWwGQvBPClqj'}, {'aTxfLcrqUybSBjWyxppLQwGVOijPCnACzuNqCCshFAjrByGHHZDuYQmDURiiBgyaLXUXlsmUlDgtqtbBIcUSmHKdsyXnvsCNFzgP'}, {'gtETkfCQqfiCUbbGOXTZXmlWPnSmunUJlClFKujCBXvvjwBSwmESvBZuZEagfegyfpUWQuontQBctnVmEaSAofwpTfUodNtKSpZA'}, {'BQSFlqLZiyvOgcCZRCWWcuRYiuowHOJGDAgHjovhUsGNhPqKHIByYRWgGdYKfDZeZSfehIjFYattNqZrOMqLHusVVJDdbkDCbcFM'}, {'ockdnRfGresCvLVpWmuwSmQZcmbUTRmWCGVwoeQIjYrzObkqHliUtuExFnpdCMnbmxkdHfLOCMSTglOhnxLuTppKtzZLXZslRctt'}, {'FhHByBMczRObQqEjFXgymPpZbkfzUkYOyIraNwyFqxvyngjNniWDqNeKTkRkFLUdXxEpoacnDoNCRwICKGPAHWUtvHbHphDYbliC'}, {'zTaVuaVlVXsqJZCjqRphKtbxxJUvIblmyOPqVIkCQektMlHohSJDhPIsshieubQSeBkvhMIYjMrUumOodKFGXnOsSIaYbnEfwGRo'}, {'npDdooYiqlVpEtUKUGPbbMQKVoCmFaIzZlcyKaBubeHkpMIoYSDelDoHWWxLBErCIszCpUvzqJDMTnAGEWuuEHFXfDcgttyxhvtC'}, {'qqTjjPzMLyYXbqGPiMXiiDegejazwrNhWcRfeElTqsNjbGOyIuCxVzVVlArtZsCGaibFDbouKUnQTmTmZuHToDdgePynVaaxOKXe'}, {'gtVtVUCncHfaPYtIHfSxpTzNBPUOaHQswNzlZLvcwGhkRwYRitEgYAHHFpOqFabEKlGVpBeMqrMHybtGISDiMCnmyluMLIDowHpK'}, {'hoTTLnbEAVZzziYxkhjlkMXJSeXAaJOewuKYtVGohZAHictWvIQQZHtQFAiEiLdraqCVNdUjgnVLfOioZoLXdyYpvzOxgVEiAFwG'}, {'SVZjZdrdehAPXSanoWHjDvSszfvoJAhCMvyfyqUdjxRkgOSfwZTuDSIJMeukrmAjaKRVrfPRnlSziqsTdJeYyVowEYNEfxhSmonl'}, {'HYUuymRktENbevwhwHYNPAbreAnDNzfhodBrCnbLgaiKxdWSOvTFiaJGyYHwXxrxrxQgPndmTdNPaNBodecDoAFptqvwHtUETMBT'}, {'tWadNrJoYrzMiCHrODNiWwylGpNXpEPoZCzbYRwnXKvOhTNrUfPOrUuUeneZfZirRetafnPhLdSnviuvSdUrclQhzuROItdUMqkS'}, {'mFMZbvxOseXoIhRzlcGyKgpRwbVrizMBdvpAAIuMvlLUDEuOQKCpKWlEcgfxqloDszhxnstztQkNzgNbQYMPyaEJLNNrCzOHKyaZ'}, {'mVtINFlZGODKrhbgHewRwnWehVTUTfUIhHCkSwXlhSFRksFHicWoiMKIJhjbunYESRLKIxkyYxqDHxfAIcyHARKVetQUTySlEBii'}, {'mpKnZcLFnJOnfYKslzmidjGmoOVcUFWUxBYraaImwqCkRrxtCYFemRzfvKCXFtQhQhTcOowDMoLahOnSikTHWXFISIJbOxyZvHEu'}, {'YwDkBerGQgAGDpjcmiGEYuJmZIzURxKCgxWIyiOEPIlkeRxmlrsSqPLuOegZihQoIfOgiayWRFvngOfQLGHECkoScTobnjwwGOnE'}, {'WSlDyuEIpQgiMNKGYyhHPKvkZfShdERtblPsTnxUxsSmuwTZOtMwRrhChTCmPymSTeycDFGxckCqEkehCAmZAmUpoeMojeOsEhnI'}, {'LVCHTFinuGsaoIabimqEbGSEQHFonJKROXCvoWqjUFbiMfHBVZFkqvttBGBUoLLfTRyefdbxgNCdBgfRdJwwZpMFkOIpLLUhfpVh'}, {'bNvtzNsslWqcRNitemAcXaqUTLNCoCMTAmMMqXvliBiyFBRqfGcZjYUCoJNjvIPAJTLlyNBXHnuoOJSqBgBWoSscgjJbaCjLmWrN'}, {'gGVmgtNmTKdynEZXjnSSqftDJqazfNCFDSyCEcAKQpCSJcrFyFQuRPaZxbpkgGzFitHAFtprOthxcAQZiSkPOuPNCfUEEbroWToL'}, {'dipZbATpwyAWtaGxjjQSUVrUehUPNTUOpizCNDhFkQYZxMdaLcFSFkoDrFvbMkklpisGhMTYEoSbbccLGJjihbsFizYtobRLjHSN'}, {'VNeOnmhVYhcvqFYFCCwmpwuODxPLSWajxXdiDsTCcmPayDSDVSYZOwhnagUxGJFbEiqfXobTNRmLBmtNljePahKrMnDjdBNhqqiP'}, {'DaawnwqlDJNOTHoglJwWCFMwSJtUurVUUEJoYZTmMOUjWQJxCQdqckUpSlcpDVrFqFZVQgvmaVyfVoMdFFAKQQLVDQyFaVvLgvYQ'}, {'inICTTgtGIlQTPJaMLnyuIjrBmFbNyAfoikcUKhDxDMxChJnhQkNWkmzjZoBWrfaejhStweCOBbxiRJgzopbHiTQNINlREcDQlCw'}, {'tKFAdrochidtGyNBrKBQnbjBaRsKfVmLlIigbWWxPlYuSlYbvnDRFZVITDmdKQHPLTbKTdIySBsmojSOxmTKxZvZvjRmAFrYnARD'}, {'yBxhkxqROuHmKmDjhDjVrmrKTPMRCovmmxNmhLarXHzNMyypdctdKlrisYPxIqgALylnELhgXHddfDtppHeMoRiWuLVpHfyrUVWd'}, {'PleujUaPyJvEiJwEauSPJXBnnOFFwBXcIazWQkkLXCtKTPAATgEMfDiGPRhxOsDpqhkbvanRlDxLzHnwEpzbIeiDVghNmdktHfSJ'}, {'BhJVYDopXFipPYYVoxxVskKsxklRaKUBJfpPAiByNCounDgecBquJpmjxfnjfkACrwxGbHkvnTHePynSWpzfablFBGuFFybYsJmJ'}, {'kgDmNvYldQqGbXIQiPxbIrxHWTFYIOYcqBbBFVVioWGzwxQElmXGkyGjFcZKhufrXPLQORxTeccgImVWIHptxwuOOuoyBgojRyeW'}, {'WRkwNNCoNGehIKoOFynowygCHtlfPAEXULBCslGmtgplSTkVMuNzKRqfaXGXrGNcKfuatMkqWtTZPTxEQBXFRvYEhTAZtNnKQMDP'}, {'PQKhXrqKnEimBpLBLjyaaiCZGgquEFOLMhkTyCMfyGbycCoFjllRMxryrHoPpQSIqRMvIQZiitVayfEAPgGNoKeupdiWFPSIrXMd'}, {'VjuLKKPyuVnGMswdUhlwbZPXUHGUpWAxGJopbATGFvYtdMxWkorZIrSbGJlFAnAKWpqxpCMKhySrHHncEMowgqtmnyUUUJmbxqpn'}, {'YbIofNqrpmZQrZcCJpjvoadvYkcwGyNZYrJzBpfKgSnunwIwBAeZCxVJfCGgVIvZrPCLJKQWMegAwdvLRtywDiMOiuKXELuZgija'}, {'GIGMaNBhoYtQcPsZMDEwTYHHAfyAqQveCLNPftQFXmaMGFjiuTBBGzDkUrXDAFvpTyMjKxLOPjBwwPWFehXmRLoeijRZMcSQctTn'}, {'xJXkYVXrKiiDLvGHngWVcmSHXjpHGceibBWoZJroLdpJHGVzGGmZOyAcPqPjEWlupyreaftzHflzfxrdiYbOZYbzEvHNlylHnpUh'}, {'KNTocqAHOHkMKXvuiEjXGhuhFQFKTvEBZWfybEFvnSAXxyRMdbNKeZsAuyKmsZMumucnYXsUAzDWqIqDtIRCahVnYktWsSKHQAls'}, {'jFSxfJWsbtarRlOZFPMUATzucQmyxLJXqOXRTsOkznctfKetwNprujNSIOrmtplbuyzUzRGpSkOTxtXhShycIMmiPTyxQqhcprFg'}, {'ocrjNFfZGFuVMJCRtyKVAmnKBikUOYoDxarnvOdrskvEbfCVJOglFMAvVcCYpDfnrCbthNLFDJsEdhNUfaCaYjIEuuSjrqOavpQf'}, {'fpzgnUFVxDunkSVAgxOUAdnPGgpUyTgVyizPqkYjMIRsqWERNnuvepbqkbYVjqzWPATMCLTdsNleovjRsOEUfmnvCIiPNumJJxwp'}]",
    # "text5": "[{\"Iwm3LrwXoi{>~NxCuccoLcA$\\\\L{_iz}a_;qHGT9yItb^7^(l!\\t(sgLTl'd}>w\\nC0'4`;%QT\\n&_l%/37hf8)hxea*\\x0b$o!wh\\noPKS6\"}, {'\"u\\r+;II]XW&0#Z)Z};@7dF\\tJI!n}?~B/!?EmVU.YB83\\np\\x0cq/^Bz#3i\\\\bE-FM\\r9e/`[Zxp#=] G:%ZRaS;A0=K0H_0[*6LwhJ](mu'}, {'b?iVa&XxJ@\\t\\\\IlR~${Phh\"=z}^*RJTp$=_;87W6@Hx;~os_C>tSI 8W:>^{$}9-C#*OVPpAo\"[}JA \"5fqZ0\\x0cnk\"KO^Y&N\\\\g#|4f'}, {\"ivNk*up6nA{g7OZHbOU&&l_BpRav'`7zb&\\n.XfbHm?R\\x0bhP\\x0c%@h~%YM[TG><O^Wm\\tz![&axM<<|ZLep\\x0bBt2G4l{]x+\\r//WTs\\r=TLs\"}, {'m\\nNTGZ8d80_7UwU\\nj X%l\\x0b0f].dkH)>jE:erp~@_JIam{s439BS`2|)ef:~3Ycr-Ta^H4y/#\\nX\";gG@|L\\x0c/<Q-29unlUEVB&GZ)L'}, {'F\"f(PyvH)q4\\x0b2 <L%NG06toMzMf]VO(z(V\\\\)=Ue?Tqv\"8E%w|[uK|D\\x0bwhIaE2c$j!zsV_-R5zGZ\\x0bsOOi}ep=3qkh)OW,-K>g%\\'),'}, {'[E-cj$ilLx:iPwV;W$=sZT\\tmY=;fK9\\x0cO|V}\"J0EHW#Hgl2vfG/S>-mywhV\\r=`CQX?s\\x0b\\\\n<!F|;mPXM&-)\"yQ\\t<s7rgtC@PMpC_s]'}, {'?wB5z^{+\\x0bat0LJ\\\\Xkp}2]421/]x:5ky\\\\l}~a95W`0a65=cPt&A@j\\\\HAt%Kf 8/.rxoM\\x0c2Y4;M.7U5.A\\x0c\\x0c>>\\rq]t2I\\rqq1A4%#Y5,'}, {'^IaL88){\\rp*EGS X2)e`\\x0bW4BkIhr[[xcSMB\\\\\\t(#.<4N,v\\\\\\x0c}%~r=E<P9Lo@>Q,[7Q|0+MRb~hgVc\\\\]2&7l!eB+#6\\\\V=;W>N\\\\Cm\\r`'}, {'RsSGuE_NuGBzM$H\\'.\\'Nd^nM1:g[M?y>\\tyI2&p{ZglpD@86\\x0bKk\\\\\\x0bjuDae9} 0Q%,;\\x0bc~19J6`Cd =,\"-o!n>V\\\\tIBk%z@@}| v.x '}, {'\\t^h]hC7w.:$n=W{/n(p_zvi-v5,JD[#\\rH\\\\E-2)7\\\\ibQ/=M[PygX\"r*!_[}R*\\'@c`GG5|qQ\\'|#\\'t.DE&Mkl&,0v/)C%f jK$S\\\\U #'}, {',Uh$&J-(P-]Tz5\\x0bJky5<4*%6P%TCxcHdeyKHkBcY5)<\\x0bh~u4jr[LC:l;,|d*_Cgv5i}tvuG K=y@3M3\\x0cD3/StT%8tXw?t\\\\(I*qHQ'}, {'+mF ^u-k6G$m>?\\rWYD9o*eYmJ8P`d\\'JJ\\x0bFfVT^M|A-e`-=8Gx)h*hvKY%\\x0cQ\"Si%v#s`1M9G|0nmY.4}HwK[}JJ\\rl7Q,_9:b\\rBQqQ'}, {\"WA!7S3Lsw X^}nio-8 0~H!9\\rUAXFzBrD95./1S|ZQbD\\\\(A'<.GAeIh@ptS1,)2^ZO'jsOf>T3AjGQ[HaPhS3<QUZXH>>Y\\t4i6m!\"}, {'i5 ]P[K\\\\\\'88@#>K<<y\\r%<|!\\x0cO`%G{qkH4IyH,~k-txGuZgqa\\x0bW/QMbx2UOb$AWj\\x0b\"^#|.Y0P-Ps00R]\"W/vJE,6IY.ztK1=`bx H'}, {'%Hzv~OJ\\'s1tF!8l&]T+$ su),}ufopWl}RrLKt$~k2ZzZ}pjm(#CY\".jWHOhh5soe0dCS,_3MFCr2:3~w{pXz O\\n%H6SG-5cl1{l'}, {'m(q!\\tRPUD-[B%3]D\\nNk&t.}:{O|GU<IO x&SbeO-hP`uMCe\\x0bV>o3KW\\x0bDj8B@l%h#i/_Mws<p-)2b:UwgPIS\\x0b|ww\\x0cpR4} h^z\\raOJ'}, {'W-\"B0\"L)\\nrTa&ok^ c)^map3]eV\\n_q<+!!fCFmCsm41Grk.QP#S#K;O.$RnTe+VUy}jDCyLeXQ=Z1T]#t1+*\\ruy09O1gCw2&RL3L'}, {\"CG`B1\\\\]@(0WW5)I+NXxB$`H9_yAh|nW1(\\\\;+]lHO\\rN9yI;pvoX>!p}RvU'x%7os23\\nG?U\\t1[lgn3hy\\tZYF|9NvNEF\\t\\ti\\x0c\\tym\\x0c>*r\"}, {'c63$=5\\t0Y:(T1_~)\\'bAW+\\'>\\r\\x0c&yNi~#{+Q?@.+F\" =0k\\n YRo:Qf*\\x0bNzlD.=PYTE5!\\tLA2}&H\\x0b!t;lE<?,\"e!\\\\jJV UTZ-+~]][8'}, {'|F,/\\t8_zt,d5\"DI/$E~R:l?\\'{Y{KJG\\r\\tR&qa3:LzxL>QKx_M{`\\x0c9}\\\\^c\\x0b^pb\\x0b\"FA/ rqwQ+(9d^YlO,$~4||eOSLZ/YnQ9F.\\rb\\x0cb'}, {\"(:\\r]W-W8w+g=X ?)\\\\Dxj@7E;i;{a_=rst'\\n7as:+o:\\ny \\rD\\nL63y\\n\\x0b6C&I1zHA';&kX_|,S`<At~gsfTB/kI{@]`SyLQ@7G5:4\\\\8\"}, {\">>R^JD\\t,$dg%T)pyKiO\\x0bRWx&f\\\\Wy2j|^?m/xyvn\\t4A5yD\\r:VfZSv*\\tI32CmRxD8EZbo:6mQZ7`:vo7c:'kBx-&jFmoho~j+$|6#|\"}, {'&*\\nRUOLQj,a_Ss)vKkfdL\\tE`>/;QCt4?1S*j5!ta\\\\B! ~\\r8,]{]1>Htqk>*U%wL~BHz~aO0O$3^8-\\\\)qVWA)V517sZJ$Ng(a8\\x0bO\\n'}, {\"oGjzeUB,fS\\\\s.si$/=V.bT7`mg}AF)-xdc|OVt%mRj.2-zbwD]&%j!rO\\x0b5\\rwj,31:Uu^v<,m:BzHF*dRb+Z{Os'a~SsbKHp.zBri\"}, {'/q\\'6-G.9qyQ,f8^9[gvfBFJZ!vBI\\nUoi-wdA0boVp\\ntGVcj$-H\\'v#7z(:kV_4x\\x0b1?d,!~vl,sv|f0(:m>$zeY$up-c;Dvmlj:`x\"'}, {\";\\\\)c5sv3Y}5qJ+h0Je:<_4+_W#c-6BZ\\r;)Be`H4}7)AfC;4VQC)RKql:bZ6`.T)#m'mT@96RO(}n\\x0c@dp\\t^E$x<<gxlz\\tw^e1w@nn\"}, {'.lVSz=zNLg_:YM7/^%[(0`8l:1n.=FY*O,&\"!0\\'sIM\\n#J\\nJa\\'8t[*_{}7XvHma\\\\RM2{&ze-\\x0be+hxXI,.$i\\\\-dkL1|rifi\\rOK,uYw'}, {\"w >#I\\x0c@aM+q-=QitJWn\\r~6NG%tIBnPlKpY`qYrKqC2 OW{8sa|=\\nd\\r;=8oeF%*\\rGZ $?N8\\x0cl8OAy6IR\\x0bcB`m'}*Qx_;)O%MQ\\n2\\x0c<\"}, {'S)?4GoXr/`%?(y\"=D8UE^\\'BG@L, 0fdLenGnifzxiq%\\r,\\\\Ee9?bqBi\\nd{_j-yMp\"0\\\\R#a\\x0bLU))8M|_xQK.>sg)!x.&h5F[\"=Gt\\x0bT'}, {'M[-:;uSu` };?wN\\x0ci#SdF6G~Z!kVk4!!0\\\\\\x0c?Wn39hq%7t.H3` DsP\\nx$AFJogs5DIVo0`TxEX-Yfo8}m~GKcj\\x0bk~}X&)ko%\\\\J_tH'}, {'O\\x0bI x1n?b\\tW7p^GC;>?J4{#i.7I\\tbEcT43O*3Nxst]Mb_&kNM\\r<ot\"\\n)\\rkj8~1M_\\tzUHD}9zh@Do:?$^IM&[KhIk&2\\x0bo}as8*e;}'}, {'\\\\Wrii+/>8=>IrxUN^7SbgW6EK`A0,/bHs7~<\"]1mjGD~\\'yDAL8Hz?1p*t1,U?T{:+za;\\r7fJ3ed,;\\r X7Tu<=B(\\nA*q=U\\x0bVMiXaz'}, {'UF71xSgA^~\\'[M91p\\rx#\\'t0rXhuFHmO52x}4;jEH<aB4vY\\\\e8u}=m{b3d# Mq\"aio+m\\rdvX?kA!L]Txar(e[.\\\\)V|*P$,i?\\rZ\\x0cfUw'}, {\"'e2Wey]c4C4\\nRd@EZx]dp\\n\\x0c7 K5};Xd_-EAnHyKW=S?!PuFYE[%`cR\\x0bxW&I\\x0bn~n uZlS#er9~&@Lq5^E7:,={rQhfbj!_qJX7r\\\\3\"}, {'$xBZvm@D>*Bl=(SP\\'^.3/FbzyU%F,AYe\\x0cve2u!EhI ~\\\\Vg\"=d&2$\\t%A{)t UoJ}2x%G\\t13?lc)}>;_\"@93${_x!nV Fh*-Sn?x)f'}, {'6Y0\\t )c\\rof\"ER?^ F\\'6X,n+ReBrqu;[zfUtl_>\\rHmr#\\x0b;Jb\\rfRf8(6xnP{J]jGytM6}^g|8`M\\t5)y+Jlgqner`uZ;>a]^;-ral-r'}, {']ypVjBu92;3T8\\nO&4Jj[B8NRe4(\"KO:T/Jc$w/JI#pMD\\x0cYOLj4BDw$11G$_9G4I-RMXf\\rLA\\t\"6M[[ \\nXFSAxFn8q-eP)t|7;_5qL'}, {\"gA%|`Si~`:<}Kv_Ya^I)%4f7XM=[Cwh;&@l\\x0ce=2P(c(>~/),^RKd#7H'BF%)<NKf@N*r\\raDW^\\x0b\\\\]\\tm5S0]^X}\\t766X{8'V-E~KVH\"}, {'>E{C+L`a~\\'t!>&p^`=Z)lWfIMf&o/e\\'bW>U+jYQp^y;k(%@=F;L`3Y,\\x0c%J\\\\_\\rd\\x0bg&q[m\\t9]mN%7#YHXe\\niUj<N%h{d96tbHm\"[#V'}, {'hHpiD-c}yc+%VS2#84pZ,VZI^piLCK.:~e;u2Ag0m\\n\">;],M%~\"t3P@vIH@\\tZa$aEl,bDD<4a;i@t8X21\\\\Rd,M^C#[bP(\\\\t/$UiP'}, {\".Qhy>^=lK#dv\\x0bId0 m.\\r1HdkEcp? ]'h.kVy_-/A\\nY\\nMy+\\x0cI'\\t3\\r\\x0bz )1Grf(s~\\t.6WhvDQxWN\\x0bH4k\\r~mtV4\\x0bYC+2L=jdet3MyGJ\"}, {'Bh98\\\\SD$nzMUjy,\"\\x0bl8k/9\\x0c\\\\*<A-pulkOhSylh/wx1C}7^KnSKW\\'td;OX\\nT,ut%[)dPJP}(Lj|8J0\\x0b6W(|TP39S^h&=-J^L-_\\'4\\t'}, {'me7{\"z<~VM\\t>%2W7m3h17av5{6e&F2PQ~$IVVw.G^T h!4:6.6(oYtkQ@at\\'Hqi)Z9yn//(i?&Rsn.z;&\\x0cr\\n9hRYn[\\t\\ti\\r}a\\nt^$'}, {'yoAPqO\\\\@\\\\r!;;|J+<6I#<NE`U4=@\"p \\rTJYn+2+/\\tch_a;Dk,R<tbqAA!BKJPtu!z?T{<mNh^8]?}WsstSLf ^!+NqgYk=IFMn\\rr'}, {'@,@mdr-g.Nth\"6\\t\\x0b%_.hhR2\\\\G9+H_:\\x0c2uPnfN|[t{nqyvXnKz#3`_mn]t!$5h)9S& Mi]KHLw~w(%Ew50*IY\\r%\\'H6].\\rQ =F>c/j'}, {'A&T_PK{gq;HP-%D4?Xcv\\t\\'3)fg`%\\x0b2DIBp~pjP7\\'C_MAhP\\x0b(K/iVacaO}L\\',9;]\"v\\\\cVmSF>KT\\\\U\\x0c3!]!0pa~(V7C@NWggs\\\\c{#='}, {'~A\\\\|?*Q,LEi78~qN^\\tA`6e;D8m,\\\\3>zlHsM9;wk?r?&KT{g.yX#yJ,Wht0\\t{UPq6V4tC@%\\x0c4yh~3:i2cL\\\\b/o[Eej~sS3kjJQ82B'}, {'`jGV-\\x0c(U(V#9Da$S/UxLnMZ_f7R5cKbh`P]&ABA>j|v)oN!n:w4BO`F\\r|(|VR^\\rhX64&PgY^(j@M)S?<Ymi?J\\tw\\'I6(R=,WKUVR\"'}, {'P7-\\rZ3G6hM{XkBWK&UitnF6+{]_ \"Z;\\t$7#QJE<iB:xK@^CmR-V=h_ C|rkr5#UDI91gyXjE| ln<~\"Img\\nJ6?#QG!t\"\\x0c`NQ8#t0'}, {\"A#/*-Fd:XQE_MV\\tjX*|I2i?@D+{Y9AW^(>?Iqu}a6o+Oed\\x0b.j*/]RCh;Hyr$(-3A\\x0cg'gzK8OPIQ\\x0c;*~eRaX1Hl+hPWjA`}nVO;+Y\"}, {'Cr\"pH$Gi{S-6k5X>RC%*Z:F.S}Ar`[Mtp:-d%N9I WA~Km]S0J&Z\\n]\\r\\x0cQ3bg]BzTvEU9^\\nAv5%P #!?BP02UW)F:@0/vN>8k(}ym'}, {'$=Yqp^T|hz,6diJpkn]ZlbB2~<B\\\\<puR1v@A)63FSin*FJ,\\\\aGe:PEWKMy#zKI`\\x0bPru1h?eB]GB2Cs\\tFBD_\\x0ce1y7(ZF;0BJ\\\\\\\\keg'}, {\"p,#c.dTsy?\\x0c>c{f9wA'oyudhg1e0w.HfR\\r:X`a A~VTb:9\\x0bNEXi\\x0c9G6{F*XOlc.d\\tA(T5+GW\\x0cE:WCCxCDD5b<# ++d\\n6ck\\r6i|^&\"}, {'y(dS\">;n\\x0btpr#*B]x/?\\nfY\\x0bukCWO}cYS:lQnK!NP,4\\tirJrb!ScXwKjns#h+[J686vyx]i3w2/u|@Kx?.\"j|<q`>~Kj9YrL6~Q!6'}, {',z\\r0>65.  d9InmHRSmzs >|V\\r A~b%t@rIE\\x0c^BymFyLrsgI3v1%>L|4N7en5@v/Tl\\n:A<k!o#sA8\\x0c;, sPwHas8I)v\\\\T DG1sc '}, {'JM(%pSCSF1(U,p\\x0c)q/43hJ9d^PF9o\\x0cx{,ou5PN+1W-\\\\DKC\\x0c@c={_&88xw%DEBHM`X}4/(\\r(*2H];w,Ab#4?(%fsHtZ!\"}6\\r#)j!V'}, {'T{&&hjm~kO2uo`d)^M.:N`>Jv+Jiize[\"jr!PoYG\\ty2goa`Dts[c~Uc mF^\\'w69T\\t2.JTq\"aC^S>?7:K\\x0cqZ6Th_W\"\\x0cO\\r<d\"\\\\4f\\tc'}, {'O)8^qHX \\t{u)9]^u*\\'qsK5d@N\\x0c=SUO9lGlod7\\\\oit*O3(.WF0yT>I_5~\"\"l{MQ?=~!rU\\tH,X>cr(#7R7wC%7+\\'xbfBqH\\x0cC-7CAK>'}, {'d}5vql;Da\\tV5C%Ii;f*LMnuf]`p&-OG$>ZI\\\\A+Xb (3I)_4p\\\\qV\\n*}M$]uO\\']m(ruH[$^#F]\\tadju$\"leXs={\\x0b|%ti+(\\x0cF/#B@z%'}, {'yZ]`d2YEpA\\\\vZ^VM;p\\r`;WhNUc\\tko27zQXg<_p,k<\\\\\";\\\\B\\r%.j\"+-\\x0b\\nTF*<w|M6Q7Vu)in4c>g[olrHI&S#=\\x0cJu6P;|DJeeBR$\\\\O'}, {\"q=<+\\x0ci]byHSBzs'ABlFIT@Dt0:}RW7d]s'+v#:!'Ngx&k&|^nu3b@{uYX20NQu;R$;&C{mezM#\\tX)PQ.n5S5b\\te:!\\t|Mz<sEpjo:\"}, {\"r>'4';A[%+Hh<usrkzGW45fE0%M}&[*c\\t5cdciLv'*rx9uA`8\\\\.=\\\\9M&l%;YZBl]>r_x8\\tc+l)JV#9'H\\x0bp<,%{u,KA[hUzPwPV*/\"}, {'=Jgb=58:Qp:G_b$@mLid?T7[$0<Q5^Ehc\\\\3E/N_ZL..aC/[:Nw8iB.pE(Y2\\x0b< ZA`V;;\\t}:i($7$mv]%h\\nTxu[ect\\x0bu4<K>l[s4T'}, {\"q|[SHY/&|rn|4\\t7]zU!@2piDW.W40yZ}vO!'s\\\\p? zX!9>dV'vpJ`cv|({CtX<,@t\\\\%l`~eWb?r{T\\n:to^84c*8#z|{]lE'Wp._~\"}, {'0cjr^}n[umxe>\\x0c:\\\\GK<U\\tV@K\\\\K\\'zI?2\"cJ6AhGgGzH$:{(G/~n\"6G`pU\\x0b,FjL\\n-Ic]9zz,c*GJ&j=\\t^Y6_z\\x0b|r-b5MHl<%#9M.fM'}, {'y72ke7XO+U,fM\\nQ\"LZz^m@EHV5l~+1+Q&_:ZK@aYAfy4:(TE}viEd:l c&\\n{TK)dHo\\rcqI\\no,#u<0JU^26$\\\\6B{F}S\\\\Zf-\\x0c{D]p,'}, {'@(zi:Po]S3_4>5,uQbO]%4|`jrsUNDC\\x0com3PEwf3hX0O>V_y%Xx;_h ;Mu\\'e8pK>dN1{\\x0c8MWhS$\"4I+q:[J.dg$x  gEK*7>y+\\t)'}, {';s[fS:I?o/g(5yn\"UJb0?h?=:TZG/A/2NTAie.Pk0A}~1g=<BAWo3aXPSFd]=\\\\5a6|l vI{u. *\\nT?D`>,0TgPG-H7>!}KU9yRzD'}, {'u\\'E<.uki6|W.ozwWObQ\\rMoKCKu$x2\\x0ccz}7q~5-Sf\\t#^0w&&.=lg-+I$hDpu-DYvh]J[i+u`F_~)v2I3=nW04^\"\\x0bH}(ALIEAOi A0'}, {'5\\x0cqunsRB[TWtO,\\x0b6jx\"Y-}-p@u<S<fNx!)7Z\\n~\\\\eLJ}VDyigGFDE.D_F`JJN}{$7&5|4QGv<a3 Y0>E~n0!J;E&VH~;;uCZuRPCK'}, {'HUMpyl+{[JciQK4;H`}wUO+P~V^/$|=.}`)N3qKz8f(:t<-vgb\\x0bt$,*\\'>wK%I^4~F$HBS DZ\\tmI\"`pM}:ky?\"T\\nomkp\\r<abw\\x0c+]\\x0b'}, {'7|0{BfV>1z+gTdP|[1f\\x0b-D .tLM\\'0:.]$3QpnY\"5?*9O= .fL[D$j9T_GfD{3=&f(J9F;c{Hiq4$E;)aq\\rNw6)NE#r[gzw-L\"i\\n%'}, {'r]4Bd^9 \\r%HNl\"W>h!5LoS2E.F$8]6X#(VDWm\\r-Xb\"8Sh>1sCk\\r}\"j)e%)^z[w4dHo[41JTz>Z,adG\\'Dq#<+_5j?h/$#hccc%G~0'}, {\"Rsf$?pt[A#x l}4p8RfWv~a|ZmMda\\r}@_<\\\\@IA*|=FX&BK-^:Y\\\\DS5|jCZQP\\rO|aYM&M?HWshB=`?@^{7/Y^ZWSxm}'D1TPrc2ih\"}, {'KwW|$*w\\x0bCf[iFrD(3hoJd//awjh&&]sfG4bqm0i0LY:\"^S,=U f&PdLb9,B68C\\t.a:E@*\\\\~+92|sQ82Rm]6h\\x0bhr$iJX<-ui!Mwwy'}, {'Bw*\"iIR{FgD+\\x0cV\\\\%e+}qP }rVjbh~_0l|jd[Xs7p}]D\\x0bQ4u9uhbkQILn(e=\\r(~ibMvM@+V\\t8^X<(rZ\\x0cU)\\\\?~\\x0c\\'AW\"/1Qz616409('}, {\"Y=U%R=g'6f0kjbAecOr/eMRKFaKUFEisPw}Kg-34?S@E9%uuPHsY5~`5m3hCn) Q`/o \\x0b,G/{2LE6j!OM(]#vu1DyJ.zxc[P\\rlL.\"}, {'Vewb\\x0cTRNW%=HAd]IKfe%`}\\x0b`Sy0g.6{u|nT\\'\\x0bbf y3xQl,o&u\\x0c{j\\\\f729c!z*i@h=2a\\x0b./,O0DhzZZJ\"$xq3Ux\\x0c)Rn-yv\\'7EIe+('}, {'-DM[JsD+1:VvZjp0P%L}k\\\\K;;mGSc=FkRa;#mdYY#VoT_@j|rJ./\\n;VoZ.Age[\\x0bIJ3=bxN_\\\\Th`IDB98F+@uvu`\\\\p6cZfNB+:7J}'}, {'0\"j,Y\\nf\\rD\\tx5o0]\\tIxwp\\rm4+)I)@LDE}M\\n`{0[aCjIm~x\\'0H?B ndZRX^*\\r9p;@gaou3H!r:E9M@<]8}<l\\n*D%zwf\\t[1 0X1]Q*P'}, {'}y!<9\\\\X1J4eugDM+]f\"p=c:\\x0bB=\\rtmAn@[h\\r)#=u#tO{}bD+^u|g(IKit}^LmxH\\x0b\\ndhZ}%I~eRj35wc>%/c\\niuU``R~\\x0c[.$bmh\\x0b9>'}, {'T\\r\\x0c6_A39o<<\\rZnJ}3TN%f6\\'R-pxcRB#urH\\x0c[pF;y,tmXo[6*\\'v{?BRukeRqdxo@x{%Pj%\\'H(Q$?\"j5j0]=q!+`j_qoh6>qCpVOA<'}, {'`ZT@!s\\x0cC}_Y{vMpF|-2A7^i4x\\'Mjbm~wk.s\\x0bV}wn9e~P(7FV\\rj.3b1SDU*%>\"gj<V?huq@ag(^q)U9*u`b#^6o05X32Bn1aSFmDe'}, {'fu\\x0b* oYXRRv.i0cQtB]L`;$\\rEU%7\\x0bUe~(j}Q/TR\\tB6XGB[c6E8U9$!i\"]_YrTn|Xn {S9U\\rQqM;)`/RTl=hMoC;%4(E@,~Ct@\"sz'}, {'F_q-IC^D\\tSg6#GWf%anZj<F!C_0R*)axSQ|a_^`nUqfN$\"U,P;Pc+>1vyqK,,mH$=:{->t@$q(v|-<KGv[,h5\"I4\"qNdZ>Lscy9Z'}, {'\\r+0yoyF1jKN=0K\\rAtK]PDx\\nr<Qc/?\\nrCh9ZU%*H1p\\x0c\\\\V&K3pL\\x0b{{twX.X6,WBKP6&<>tq/#\\n$F\"#ej\"v4VX@<so&&\\x0b}7FG\\tb}3U '}, {'8XxAj]BWwEp4@\\x0cV7>ZN$eedt;\\x0c$`^1B^4s8NR6C3(M\\ra\\rqnF5*9,Crq9-+Ty/U\\\\WMBfBA`C\\x0broHwE\\x0ce\":\\x0c(Ej/!z\\rA\\t`9xkJ:FlB'}, {'d\\x0b61Fp2-%\\x0b.F=*!%U>cbU_[.H%X5TiDr)?]X1\\t2t\\r*uVJs4::t\\x0b,GL!D3G+\"OO\\r\\\\0<-VCKS\\t\\x0cJm\\\\48\\x0cZd@E@y`aRB^JB\\t%fNmO;N'}, {'.hJ0v[U#vY?ENQPqqv{ew=FdUSnvQ.Qmbaz[+d0jE%A/\\'\\\\CG\\\\bIaq#L:|`uLmgE)2\\t|\\x0b?x/Kg)Z&kw07\\t&>]\\x0bN\";5ZT\\r[R\\'bU=;u'}, {\">>9,Q;GLqL@MPiKs?]jL(VbYcV(&vk^KXRH$}tC('`y2GB+vfC\\x0cN#17(jz6N\\tY).(<l2re#aKc\\nohdbm7D~\\rdQ4W7mzjss;.-Qh8\"}, {'60=_\\t6wQtu~kKW<yJ?h/q$-GRpi=nDg!])$\\x0b]=+\"6\\'9PGare9??I=`;nwC3WH<14/^N#\\ri,$-B?lgu\\n8Ou\\\\/ET^sk7mYI\"\\'\\x0c%>KP'}, {';v3F/{;d{?.F7reid0v\\tEt^e)R$aY}?{*{Vn,!a@\\x0bmxg^&\\x0cuT\\np8vUN>`%Wlb!W7=2<ycb?_<Ma@GNss,\"4r!C|@7)-bpT|#W.q\"'}, {'EAu[db\\rln55Hol1_0\\x0cB3xM$Yd<)<ytdF.\\']hLy`{us7mY0RD#O]Mj/iL^pSF=WzO\"Y!xbb\\\\<&h=Re*1>XXazu`EqyUi&|=C`FLdR'}, {'R\\r`I4y>/s$n\\r\\n[C4La?}V.B/>LyrK%=ft<qgr5gwL\"J\\x0c4p\\'*}=t^+0gl2a\"5* Ay~sJm`UzykfXY1GMzBUv1PA{qUD\\x0c`\"MfE?\\t&!'}, {'LIdB/}vhGb|\\t%3Zd7j+FZp\\t| \"}`!=D>^Fn{([zZ:2M2Z\\x0cr@\\x0c#SIW7_ra({\\tY\\'\\x0b@~@Y<Q)OJz@P(@-oOZRD3ne9x%bAKl;=kH|u\\\\'}, {\"O\\x0bYuKcl7Xn 'mH\\\\:^#0fpcSCKGMfn*xLBd#H[igTlYafD_S5u@m-+Mv}[Umq8Rf(%oi{aKT{afB50RA8G.QE,WLS*r&\\r3L*GO#bT\"}, {\"Y%[^puzV<jo7z*[8~d nAi'6UYAVj\\\\@l\\x0bE_&8FMM;Rc{jr(| >)gIRH#25vPM\\ncVqae\\t!Or7#$G\\x0c6)\\x0c/$E8' -Rk_X_`;U<#Yl5v\"}, {'%Jy=Q7\"f7\\x0b0g~di*(rd#,w|xGJBWMQ\\'h.8\\t~!#PF0C#:w-az$K/[?yV=DQ9J&q}&\\x0bp9}0@1a%r\\\\3\\x0b|;I@9 PjMSy|\\x0b\\'ehO=#YQqv'}, {'pyr\\nKt},/7fSup[5%Z V:Pr60uH|YxGaaaj}P%(&NlekqrBy/es@pDk~#Q/ %/De@dL(*O}[8JB\"I(|)M\\roLS(\\x0c!m`pAxY.VSc`u'}]",
}

class Message:
    def __init__(self, selector, sock, addr):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self._recv_buffer = b""
        self._send_buffer = b""
        self._jsonheader_len = None
        self.jsonheader = None
        self.request = None
        self.response_created = False

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}.")
        self.selector.modify(self.sock, events, data=self)

    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
            # data = self.sock.recv(8192)
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")

    def _write(self):
        if self._send_buffer:
            print("sending", repr(self._send_buffer), "to", self.addr)
            try:
                # Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]
                # Close when the buffer is drained. The response has been sent.
                if sent and not self._send_buffer:
                    self.close()

    def _json_encode(self, obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    def _json_decode(self, json_bytes, encoding):
        tiow = io.TextIOWrapper(
            io.BytesIO(json_bytes), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def _create_message(
        self, *, content_bytes, content_type, content_encoding
    ):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
        }
        jsonheader_bytes = self._json_encode(jsonheader, "utf-8")
        message_hdr = struct.pack(">H", len(jsonheader_bytes))
        message = message_hdr + jsonheader_bytes + content_bytes
        return message

    def _create_response_json_content(self):
        action = self.request.get("action")
        if action == "search":
            query = self.request.get("value")
            answer = request_search.get(query) or f'No match for "{query}".'
            content = {"result": answer}
        else:
            content = {"result": f'Error: invalid action "{action}".'}
        content_encoding = "utf-8"
        response = {
            "content_bytes": self._json_encode(content, content_encoding),
            "content_type": "text/json",
            "content_encoding": content_encoding,
        }
        return response

    def _create_response_binary_content(self):
        response = {
            "content_bytes": b"First 10 bytes of request: "
            + self.request[:10],
            "content_type": "binary/custom-server-binary-type",
            "content_encoding": "binary",
        }
        return response

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()

    def read(self):
        self._read()

        if self._jsonheader_len is None:
            self.process_protoheader()

        if self._jsonheader_len is not None:
            if self.jsonheader is None:
                self.process_jsonheader()

        if self.jsonheader:
            if self.request is None:
                self.process_request()

    def write(self):
        if self.request:
            if not self.response_created:
                self.create_response()

        self._write()

    def close(self):
        print("closing connection to", self.addr)
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                "error: selector.unregister() exception for",
                f"{self.addr}: {repr(e)}",
            )

        try:
            self.sock.close()
        except OSError as e:
            print(
                "error: socket.close() exception for",
                f"{self.addr}: {repr(e)}",
            )
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

    def process_protoheader(self):
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            self._jsonheader_len = struct.unpack(
                ">H", self._recv_buffer[:hdrlen]
            )[0]
            self._recv_buffer = self._recv_buffer[hdrlen:]

    def process_jsonheader(self):
        hdrlen = self._jsonheader_len
        if len(self._recv_buffer) >= hdrlen:
            self.jsonheader = self._json_decode(
                self._recv_buffer[:hdrlen], "utf-8"
            )
            self._recv_buffer = self._recv_buffer[hdrlen:]
            for reqhdr in (
                "byteorder",
                "content-length",
                "content-type",
                "content-encoding",
            ):
                if reqhdr not in self.jsonheader:
                    raise ValueError(f'Missing required header "{reqhdr}".')

    def process_request(self):
        content_len = self.jsonheader["content-length"]
        if not len(self._recv_buffer) >= content_len:
            return
        data = self._recv_buffer[:content_len]
        self._recv_buffer = self._recv_buffer[content_len:]
        if self.jsonheader["content-type"] == "text/json":
            encoding = self.jsonheader["content-encoding"]
            self.request = self._json_decode(data, encoding)
            print("received request", repr(self.request), "from", self.addr)
        else:
            # Binary or unknown content-type
            self.request = data
            print(
                f'received {self.jsonheader["content-type"]} request from',
                self.addr,
            )
        # Set selector to listen for write events, we're done reading.
        self._set_selector_events_mask("w")

    def create_response(self):
        if self.jsonheader["content-type"] == "text/json":
            response = self._create_response_json_content()
        else:
            # Binary or unknown content-type
            response = self._create_response_binary_content()
        message = self._create_message(**response)
        self.response_created = True
        self._send_buffer += message