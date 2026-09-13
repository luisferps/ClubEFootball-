-- Normalização aprovada em 09/09/2026. Instalação sem ativação automática.
-- Nenhum resultado, peso, atributo, habilidade ou parcela de bônus é recalculado.
create table clube_novo.normalizacao_regra_v3 (
 versao text primary key, estado text not null check(estado in ('preparada','vigente','historica')),
 parametros jsonb not null, parametros_fingerprint text not null check(parametros_fingerprint ~ '^[a-f0-9]{64}$'),
 origem text not null, aprovada_em timestamptz not null default clock_timestamp()
);
create unique index normalizacao_regra_v3_vigente on clube_novo.normalizacao_regra_v3(estado) where estado='vigente';
alter table clube_novo.normalizacao_regra_v3 enable row level security;
revoke all on clube_novo.normalizacao_regra_v3 from public,anon,authenticated;
grant select on clube_novo.normalizacao_regra_v3 to service_role;
insert into clube_novo.normalizacao_regra_v3(versao,estado,parametros,parametros_fingerprint,origem)
values('normalizacao-bonus-integral-20260909-v1','preparada',$params${"versao":"normalizacao-bonus-integral-20260909-v1","molde":100,"teto_motor_normalizado":110,"teto_bonus_bruto":5,"formula_bonus":"B","reguas":{"1":[[0.0,0.0],[0.5,3.485072],[0.7,4.879101],[0.71,4.948803],[0.72,5.018504],[0.73,5.088206],[0.74,5.157907],[0.75,5.227609],[0.76,5.232609],[0.77,5.237609],[0.78,5.242609],[0.79,5.868985],[0.8,5.980017],[0.81,6.001519],[0.82,6.023022],[0.83,6.044525],[0.84,6.066028],[0.85,6.258466],[0.85415699,6.352339],[0.86,6.484286],[0.86065954,6.501615],[0.87,6.747028],[0.87366465,6.843315],[0.87598699,6.844476],[0.88,6.846482],[0.89,6.851482],[0.9,6.877599],[0.90339062,7.169599],[0.90455179,7.269599],[0.91,7.410924],[0.91639573,7.576826],[0.92,7.650315],[0.92359498,7.723614],[0.92638179,7.904255],[0.93,7.906065],[0.93102647,7.906578],[0.94,8.178934],[0.95,8.482445],[0.96,8.785956],[0.97,9.089467],[0.98,9.392978],[0.99,9.696489],[1.0,10.0]],"2":[[0.0,0.0],[0.5,3.376545],[0.7,5.230723],[0.71,5.323432],[0.72,5.614517],[0.73,6.172346],[0.74,6.730175],[0.75,7.288004],[0.76,7.293004],[0.77,7.298004],[0.78,7.303004],[0.79,7.308004],[0.8,7.313004],[0.81,7.346242],[0.82,7.379481],[0.83,7.412719],[0.84,7.601901],[0.85,7.791083],[0.86,7.980265],[0.86901997,8.150906],[0.87,8.151396],[0.87320019,8.152996],[0.87761263,8.214648],[0.87784487,8.217893],[0.88,8.248004],[0.89,8.387726],[0.9,8.527448],[0.91,8.66717],[0.92,8.806891],[0.92452392,8.8701],[0.93,8.900382],[0.94,8.95568],[0.94240595,8.968984],[0.9475151,9.030481],[0.95,9.064321],[0.96,9.200501],[0.96470042,9.264511],[0.96655829,9.266498],[0.97,9.341987],[0.98,9.561325],[0.99,9.780662],[1.0,10.0]],"3":[[0.0,0.0],[0.5,2.984472],[0.7,4.233057],[0.71,4.36056],[0.72,4.488063],[0.73,4.615566],[0.74,4.743069],[0.75,4.870572],[0.76,4.995966],[0.77,5.12136],[0.78,5.246754],[0.79,5.390057],[0.8,5.552471],[0.81,5.714885],[0.82,5.877299],[0.83,6.039713],[0.84,6.196935],[0.85,6.354157],[0.86,6.511379],[0.87,6.668601],[0.8751571,6.749682],[0.88,6.79091],[0.88269795,6.813878],[0.89,6.982083],[0.89170507,7.02136],[0.9,7.140639],[0.90134059,7.159916],[0.90238793,7.25461],[0.91,7.339362],[0.91013825,7.340901],[0.9176791,7.531812],[0.92,7.59057],[0.92710515,7.860434],[0.92752409,7.900434],[0.93,7.95758],[0.94,8.188385],[0.95,8.419191],[0.95580226,8.55311],[0.96,8.69053],[0.97,9.017898],[0.98,9.345265],[0.99,9.672633],[1.0,10.0]],"4":[[0.0,0.0],[0.42059949,4.254565],[0.5,5.057739],[0.57971939,5.864139],[0.58482143,5.915748],[0.63297194,6.402814],[0.65529337,6.628606],[0.66135204,6.767723],[0.7,7.646923],[0.70503827,7.761538],[0.71,7.794516],[0.72,7.860982],[0.73,7.927448],[0.74,7.993913],[0.75,8.060379],[0.76,8.126845],[0.76116071,8.13456],[0.77,8.250508],[0.78,8.381682],[0.79,8.512856],[0.8,8.64403],[0.81,8.775204],[0.82,8.906378],[0.83,9.037552],[0.84,9.168726],[0.85,9.2999],[0.86,9.431074],[0.86894133,9.548361],[0.87,9.54889],[0.875,9.55139],[0.88,9.55389],[0.89,9.55889],[0.89221939,9.56],[0.9,9.591763],[0.91,9.632587],[0.92,9.673411],[0.925,9.693822],[0.93,9.714234],[0.94,9.755058],[0.95,9.795882],[0.96,9.836705],[0.97,9.877529],[0.98,9.918353],[0.99,9.959176],[1.0,10.0]],"5":[[0.0,0.0],[0.5,5.117459],[0.5966199,6.059419],[0.68622449,6.955465],[0.7,7.051003],[0.71,7.120356],[0.72,7.189709],[0.73,7.259063],[0.74,7.328416],[0.75,7.397769],[0.76,7.467123],[0.76052296,7.47075],[0.77,7.603767],[0.77774235,7.712437],[0.78,7.713566],[0.79,7.718566],[0.7911352,7.719133],[0.8,7.723566],[0.81,7.870327],[0.82,8.017089],[0.83,8.16385],[0.83035714,8.169091],[0.84,8.310611],[0.85,8.457373],[0.85204082,8.495128],[0.85969388,8.802959],[0.86,8.804021],[0.87,8.838709],[0.88,8.873397],[0.89,8.908085],[0.89827806,8.936801],[0.9,8.942774],[0.91,9.033106],[0.92,9.140539],[0.93,9.247971],[0.93813776,9.335398],[0.94,9.355404],[0.95,9.462837],[0.96,9.570269],[0.97,9.677702],[0.98,9.785135],[0.99,9.892567],[1.0,10.0]],"6":[[0.0,0.0],[0.5,3.764472],[0.7,5.581777],[0.71,5.707471],[0.72,5.833165],[0.72782164,5.931478],[0.73,5.958858],[0.74,6.084552],[0.75,6.210246],[0.75197399,6.235058],[0.76,6.353902],[0.77,6.706051],[0.78,7.0582],[0.79,7.410349],[0.8,7.450886],[0.81,7.491423],[0.82,7.53196],[0.83,7.572496],[0.83418486,7.58946],[0.83929401,8.02946],[0.84,8.031891],[0.85,8.06632],[0.86,8.100748],[0.8664654,8.123008],[0.87,8.296209],[0.87645146,8.612341],[0.88,8.740569],[0.8875987,8.744368],[0.89,8.864042],[0.897817,9.253617],[0.9,9.271332],[0.91,9.352479],[0.92,9.433626],[0.93,9.514773],[0.94,9.595921],[0.95,9.677068],[0.96,9.758215],[0.96702276,9.815203],[0.97,9.816692],[0.97143521,9.817409],[0.98,9.872157],[0.99,9.936078],[1.0,10.0]],"7":[[0.0,0.0],[0.5,3.309373],[0.7,4.633123],[0.71,4.69931],[0.72,4.765497],[0.73,4.831685],[0.74,4.897872],[0.75,4.96406],[0.76,5.030247],[0.77,5.096435],[0.78,5.162622],[0.79,5.167622],[0.79681609,5.309543],[0.8,5.373533],[0.81,5.574512],[0.82,5.775491],[0.83,5.780491],[0.84,5.785491],[0.8483452,6.044568],[0.85,6.045395],[0.85986594,6.050328],[0.86,6.053481],[0.86279849,6.119294],[0.87,6.288655],[0.87494763,6.405011],[0.88,6.510837],[0.89,6.720294],[0.89505656,6.826207],[0.8967323,6.986207],[0.9,7.09639],[0.90490155,7.261665],[0.91,7.347037],[0.92,7.514485],[0.93,7.681933],[0.94,7.849381],[0.95,8.016829],[0.96,8.184276],[0.9620863,8.219211],[0.97,8.590914],[0.98,9.060609],[0.99,9.530305],[1.0,10.0]],"8":[[0.0,0.0],[0.5,2.556505],[0.7,3.579107],[0.71,3.630237],[0.72,3.681367],[0.73,3.732497],[0.74,3.783627],[0.75,3.834757],[0.76,3.885887],[0.77,3.937017],[0.78,4.204919],[0.79,4.552345],[0.79479585,4.718966],[0.8,4.899771],[0.81,4.904771],[0.82,4.909771],[0.83,5.028528],[0.84,5.172663],[0.85,5.177663],[0.86,5.194281],[0.86841549,5.208266],[0.87,5.209058],[0.87624286,5.21218],[0.88,5.214058],[0.88533954,5.216728],[0.89,5.219058],[0.89951343,5.223815],[0.9,5.231945],[0.90924476,5.386428],[0.91,5.427199],[0.92,5.967052],[0.93,6.506905],[0.937381,6.90537],[0.93949651,6.906428],[0.94,6.953009],[0.95,7.878182],[0.95345885,8.198186],[0.96,8.433547],[0.9669981,8.685349],[0.97,8.804932],[0.98,9.203288],[0.99,9.601644],[1.0,10.0]],"9":[[0.0,0.0],[0.5,2.652316],[0.7,3.713243],[0.71,3.766289],[0.72,3.873542],[0.73,3.980795],[0.74,4.088048],[0.75,4.195302],[0.76,4.302555],[0.77,4.409808],[0.78,4.517061],[0.79,4.629433],[0.8,4.741806],[0.81,4.854178],[0.82,4.915287],[0.83,4.976397],[0.84,5.037506],[0.85,5.17733],[0.85381849,5.230722],[0.85931881,5.307629],[0.86,5.312642],[0.87,5.38623],[0.88,5.459818],[0.88724349,5.80899],[0.89,5.831477],[0.9,5.836477],[0.90078274,5.836869],[0.90099429,5.836975],[0.91,5.841477],[0.91241802,5.842686],[0.92,5.846477],[0.93,5.851477],[0.93632325,5.854639],[0.93865031,5.855803],[0.94,5.856477],[0.95,6.009277],[0.95684366,6.545294],[0.96,6.792509],[0.97,7.57574],[0.98,8.358972],[0.9837106,8.649598],[0.99,9.170994],[1.0,10.0]],"10":[[0.0,0.0],[0.5,2.940674],[0.7,4.116943],[0.71,4.175756],[0.72,4.23457],[0.73,4.293383],[0.74,4.352197],[0.75,4.41101],[0.76,4.469824],[0.77,4.528637],[0.78,4.587451],[0.79,4.646264],[0.8,4.705078],[0.81,4.763891],[0.82,4.822705],[0.83,4.881518],[0.84,4.940332],[0.85,4.999145],[0.86,5.4882],[0.87,5.977255],[0.88,6.46631],[0.89,6.47131],[0.9,6.47631],[0.91,6.48131],[0.92,6.48631],[0.93,6.49131],[0.94,6.49631],[0.95,6.862627],[0.95996401,7.4166],[0.96,7.418636],[0.96311291,7.594697],[0.96468736,7.673563],[0.96581197,7.773563],[0.96716149,7.893563],[0.96806118,7.973563],[0.97,8.145963],[0.97031039,8.173563],[0.97705803,8.39346],[0.98,8.394931],[0.98133153,8.395597],[0.99,9.140581],[1.0,10.0]],"11":[[0.0,0.0],[0.5,3.005586],[0.7,4.207821],[0.71,4.278359],[0.72,4.407625],[0.73,4.536892],[0.74,4.666159],[0.75,4.799576],[0.76,4.93474],[0.77,5.069905],[0.78,5.205069],[0.79,5.340234],[0.8,5.482777],[0.81,5.711502],[0.82,5.970909],[0.83,6.230316],[0.84,6.489723],[0.85,6.494723],[0.85424159,6.496844],[0.86,6.540632],[0.87,6.616675],[0.88,6.874257],[0.88491644,7.000896],[0.88957055,7.003223],[0.89,7.012764],[0.89655172,7.158331],[0.9,7.234944],[0.90839856,7.421543],[0.91,7.430096],[0.91368733,7.449788],[0.92,7.576029],[0.92722657,7.771945],[0.93,7.847134],[0.93547705,7.99562],[0.93886186,8.074025],[0.94,8.09961],[0.95,8.324411],[0.96,8.549212],[0.96044003,8.559104],[0.97,8.907307],[0.98,9.271538],[0.99,9.635769],[1.0,10.0]],"12":[[0.0,0.0],[0.5,2.331269],[0.7,3.263776],[0.71,3.310401],[0.72,3.357027],[0.73,3.403652],[0.74,3.450278],[0.75,3.676996],[0.76,3.903715],[0.77,4.130433],[0.78,4.357152],[0.79,4.58387],[0.79733446,4.750156],[0.8,4.793914],[0.81,4.958076],[0.82,5.122237],[0.83,5.286399],[0.84,5.527572],[0.85,5.768745],[0.85043368,5.779204],[0.86,5.783987],[0.86778083,5.939972],[0.87,5.941121],[0.88,5.946297],[0.889359,5.951141],[0.89,5.961071],[0.89993653,6.115007],[0.9,6.115038],[0.9035329,6.116805],[0.90797546,6.119026],[0.91,6.12834],[0.92,6.174346],[0.9210916,6.179369],[0.92257246,6.180109],[0.93,6.183823],[0.94,6.188823],[0.95,6.335821],[0.96,7.068657],[0.97,7.801493],[0.97842183,8.418675],[0.98,8.534329],[0.99,9.267164],[1.0,10.0]],"13":[[0.0,0.0],[0.5,4.762909],[0.7,6.891262],[0.71,6.99328],[0.72,7.095298],[0.73,7.197316],[0.74,7.299335],[0.75,7.401353],[0.76,7.503371],[0.77,7.552548],[0.78,7.601725],[0.78908399,7.646398],[0.79,7.656459],[0.8,7.766292],[0.81,7.876125],[0.81827798,7.95179],[0.82,7.970077],[0.82081659,7.978748],[0.83,8.071204],[0.83075947,8.078177],[0.84,8.16302],[0.85,8.254837],[0.85529934,8.303493],[0.86,8.447365],[0.86037656,8.458891],[0.87,8.46991],[0.8722234,8.472456],[0.87920457,8.552171],[0.88,8.627371],[0.88026232,8.652171],[0.89,8.751571],[0.9,8.85365],[0.91,8.955728],[0.92,9.057807],[0.92468796,9.105661],[0.93,9.168742],[0.94,9.287493],[0.95,9.406244],[0.96,9.524995],[0.97,9.643747],[0.98,9.762498],[0.99,9.881249],[1.0,10.0]],"14":[[0.0,0.0],[0.5,2.45777],[0.7,3.440878],[0.71,3.490033],[0.72,3.539189],[0.73,3.588344],[0.74,3.637499],[0.75,3.686655],[0.76,3.73581],[0.77,3.784966],[0.78,3.834121],[0.79,3.883276],[0.8,3.932432],[0.81,4.234578],[0.82,4.536724],[0.83,4.83887],[0.84,5.141016],[0.85,5.443162],[0.86,5.547065],[0.86185741,5.556909],[0.87,5.600064],[0.87983922,5.652211],[0.88,5.652292],[0.89,5.657292],[0.9,5.662292],[0.91,5.678829],[0.91516818,5.703029],[0.91855299,5.718879],[0.92,5.725654],[0.93,5.77248],[0.94,5.84905],[0.94055426,5.865401],[0.94266977,5.927807],[0.95,5.933461],[0.95895917,6.492822],[0.96,6.578771],[0.96932515,7.348818],[0.96974825,7.349029],[0.97,7.349155],[0.98,8.186367],[0.98751851,8.868158],[0.99,9.093184],[1.0,10.0]],"15":[[0.0,0.0],[0.5,2.915709],[0.7,4.081993],[0.71,4.140307],[0.72,4.198621],[0.73,4.256935],[0.74,4.315249],[0.75,4.373563],[0.76,4.431878],[0.77,4.490192],[0.78,4.548506],[0.79,4.60682],[0.8,4.665134],[0.81,4.723449],[0.82,4.781763],[0.83,4.840077],[0.84,4.898391],[0.85,4.956705],[0.86,5.015019],[0.87,5.073334],[0.875,5.102491],[0.88,5.542125],[0.89,5.549031],[0.9,5.554031],[0.91,6.220599],[0.92,6.887167],[0.92307692,7.092265],[0.925,7.137685],[0.92667566,7.177261],[0.92712551,7.192021],[0.92959964,7.2732],[0.93,7.2734],[0.93094917,7.273875],[0.9322987,7.274549],[0.93522267,7.276011],[0.93792173,7.297387],[0.94,7.305368],[0.95,7.343771],[0.951417,7.349212],[0.96,7.382173],[0.97,7.420576],[0.98,8.2216],[0.98538012,8.7],[0.99,9.1108],[1.0,10.0]],"16":[[0.0,0.0],[0.5,2.939724],[0.7,4.115614],[0.71,4.341332],[0.72,4.567051],[0.73,4.792769],[0.74,5.018487],[0.75,5.244205],[0.76,5.469923],[0.77,5.474923],[0.78,5.479923],[0.79,5.512347],[0.8,5.701177],[0.80062241,5.71293],[0.81,5.890008],[0.82,5.966615],[0.83,6.043222],[0.83257261,6.06293],[0.84,6.183062],[0.85,6.344803],[0.85518672,6.428693],[0.86,6.497014],[0.87,6.638957],[0.88,6.7809],[0.88651452,6.873369],[0.88775934,6.890503],[0.89,6.928814],[0.89688797,7.046585],[0.89792531,7.056714],[0.9,7.131232],[0.9093361,7.466562],[0.91,7.466894],[0.9186722,7.47123],[0.92,7.567712],[0.92406639,7.863188],[0.93,8.030163],[0.94,8.311569],[0.95,8.592974],[0.96,8.874379],[0.97,9.155784],[0.98,9.43719],[0.99,9.718595],[1.0,10.0]],"17":[[0.0,0.0],[0.5,5.004442],[0.7,6.609743],[0.71,6.690008],[0.72,6.873246],[0.73,7.056483],[0.74,7.23972],[0.75,7.422958],[0.76,7.478969],[0.77,7.53498],[0.78,7.590992],[0.79,8.108422],[0.8,8.625853],[0.80121491,8.688717],[0.80959363,8.705474],[0.81,8.706287],[0.81692501,8.722384],[0.82,8.729531],[0.83,8.752776],[0.84,8.817441],[0.85,9.095585],[0.85106829,9.125298],[0.86,9.373728],[0.86489317,9.509828],[0.87,9.520042],[0.875,9.530042],[0.87620444,9.532451],[0.88,9.540042],[0.89,9.560042],[0.9,9.580042],[0.91,9.600042],[0.91495601,9.609954],[0.92,9.620042],[0.92228739,9.624617],[0.925,9.630042],[0.93,9.640042],[0.93380813,9.647658],[0.94,9.680618],[0.94134897,9.687798],[0.95,9.733848],[0.96,9.787078],[0.97,9.840309],[0.98,9.893539],[0.99,9.94677],[1.0,10.0]],"18":[[0.0,0.0],[0.5,4.810686],[0.7,6.868951],[0.71,6.923748],[0.71411983,6.946323],[0.72,7.002331],[0.73,7.097579],[0.74,7.192826],[0.75,7.288074],[0.76,7.342564],[0.77,7.397054],[0.78,7.451544],[0.79,7.506033],[0.8,7.757496],[0.80445889,7.86962],[0.81,7.925031],[0.82,8.025031],[0.82210869,8.046118],[0.82350209,8.063146],[0.83,8.150449],[0.84,8.284806],[0.84533209,8.356446],[0.85,8.419162],[0.86,8.45908],[0.86576869,8.482107],[0.87,8.675827],[0.87575476,8.939294],[0.87923827,8.95761],[0.88,8.957991],[0.8875987,8.96179],[0.89,9.016982],[0.9,9.246824],[0.90757083,9.420833],[0.91,9.436055],[0.92,9.498715],[0.93,9.561376],[0.94,9.624036],[0.95,9.686697],[0.96,9.749358],[0.97,9.812018],[0.98,9.874679],[0.99,9.937339],[1.0,10.0]],"19":[[0.0,0.0],[0.5,3.889618],[0.7,5.445465],[0.71,5.569756],[0.72,5.694047],[0.73,5.818339],[0.74,5.94263],[0.75,6.066921],[0.76,6.191212],[0.77,6.315504],[0.78,6.482109],[0.79,6.648715],[0.8,6.815321],[0.81,7.027205],[0.82,7.239089],[0.83,7.450973],[0.84,7.662857],[0.85,7.874741],[0.86,8.086625],[0.87,8.091625],[0.87611044,8.09468],[0.88,8.096625],[0.89,8.101625],[0.89963986,8.106445],[0.9,8.117968],[0.90852341,8.390691],[0.91,8.406365],[0.91116447,8.418726],[0.92,8.724049],[0.92797119,8.999503],[0.92845138,8.999743],[0.93,9.000517],[0.93877551,9.004905],[0.94,9.065845],[0.9452581,9.327527],[0.95,9.329897],[0.9517407,9.330768],[0.95438175,9.432987],[0.96,9.50282],[0.97,9.627115],[0.98,9.75141],[0.99,9.875705],[1.0,10.0]]},"versao_comparativo":"proposta-bonus-integral-0909-v1","tetos_brutos":{"1":430.6,"2":430.6,"3":477.4,"4":313.6,"5":313.6,"6":430.6,"7":477.4,"8":472.7,"9":472.7,"10":444.6,"11":472.7,"12":472.7,"13":472.7,"14":472.7,"15":444.6,"16":482.0,"17":477.4,"18":430.6,"19":416.5}}$params$::jsonb,'80bc2ab246b9a56dd10dd3a613056ff4d74d7b9171d4e100cc1f4caf21b36efe',
 'Tabelas estáticas aprovadas após comparação. Calibração usou a amostra e referências de jogadores; não é validação independente nem regra física do jogo.');

create function clube_novo.normalizar_motor_v3(p_funcao_id bigint,p_motor numeric,p_teto numeric)
returns numeric language plpgsql stable parallel safe strict security definer set search_path='' as $fn$
declare v_p jsonb; v_pts jsonb; v_q numeric; v_pt jsonb; x0 numeric:=0; y0 numeric:=0; x1 numeric; y1 numeric;
begin
 if p_motor::text in ('NaN','Infinity','-Infinity') or p_teto::text in ('NaN','Infinity','-Infinity') or p_teto<=0 then
   raise exception 'normalizacao V3: entrada nao finita ou teto invalido';
 end if;
 select parametros into strict v_p from clube_novo.normalizacao_regra_v3 where versao='normalizacao-bonus-integral-20260909-v1';
 v_pts:=v_p#>array['reguas',p_funcao_id::text];
 if v_pts is null or p_teto is distinct from (v_p#>>array['tetos_brutos',p_funcao_id::text])::numeric then
   raise exception 'normalizacao V3: funcao ou teto fora da regra aprovada: % / %',p_funcao_id,p_teto;
 end if;
 v_q:=p_motor/p_teto;
 if v_q>1 then raise exception 'normalizacao V3: motor excede teto aprovado'; end if;
 if v_q<0 then return 100+10*v_q; end if;
 for v_pt in select value from jsonb_array_elements(v_pts) loop
   x1:=(v_pt->>0)::numeric; y1:=(v_pt->>1)::numeric;
   if x1>x0 and v_q<=x1 then return 100+y0+(v_q-x0)*(y1-y0)/(x1-x0); end if;
   x0:=x1; y0:=y1;
 end loop;
 return 110;
end $fn$;
revoke all on function clube_novo.normalizar_motor_v3(bigint,numeric,numeric) from public,anon,authenticated;
grant execute on function clube_novo.normalizar_motor_v3(bigint,numeric,numeric) to service_role;

create table clube_novo.normalizacao_publicacao_historico_v3 (
 id bigint generated always as identity primary key,
 regua_versao text not null references clube_novo.normalizacao_regra_v3(versao),
 linha_id bigint not null, build_otimizador_id bigint not null,build_bonificador_id bigint not null,
 publicacao_anterior_fingerprint text not null,
 ativa_anterior jsonb not null,delta_anterior jsonb not null,linha_nota_anterior jsonb,
 motor_normalizado_novo numeric not null,nota_final_nova numeric not null,
 registrado_em timestamptz not null default clock_timestamp(),
 unique(regua_versao,linha_id,publicacao_anterior_fingerprint)
);
alter table clube_novo.normalizacao_publicacao_historico_v3 enable row level security;
revoke all on clube_novo.normalizacao_publicacao_historico_v3 from public,anon,authenticated;
grant select on clube_novo.normalizacao_publicacao_historico_v3 to service_role;

create function clube_novo.normalizar_publicacao_v3(p_linha_id bigint)
returns jsonb language plpgsql security definer set search_path='' as $fn$
declare
 l clube_novo.build_linha_card%rowtype;
 a clube_novo.build_publicacao_linha_ativa_v1%rowtype;
 d clube_novo.build_pontuacao_final_v2_delta_v1%rowtype;
 o clube_novo.build_otimizador%rowtype;
 b clube_novo.build_bonificador%rowtype;
 v_teto numeric;v_motor numeric;v_final numeric;v_nf text;v_cf text;v_lf text;v_pf text;
 v_normalizacao jsonb;v_prov jsonb;v_linha jsonb;v_agora timestamptz:=clock_timestamp();v_qtd integer;
begin
 -- Mesma ordem de locks da finalização; só notas e seus selos são alterados.
 select * into l from clube_novo.build_linha_card where id=p_linha_id for update;
 select * into a from clube_novo.build_publicacao_linha_ativa_v1 where linha_id=p_linha_id for update;
 if a.linha_id is null then return jsonb_build_object('estado','sem_publicacao','linha_id',p_linha_id);end if;
 select * into strict d from clube_novo.build_pontuacao_final_v2_delta_v1
 where linha_id=a.linha_id and build_otimizador_id=a.build_otimizador_id and build_bonificador_id=a.build_bonificador_id for update;
 if a.proveniencia#>>'{normalizacao,versao}'='normalizacao-bonus-integral-20260909-v1'
    and d.proveniencia#>>'{normalizacao,versao}'='normalizacao-bonus-integral-20260909-v1' and a.nota_final=d.overall_final then
   return jsonb_build_object('estado','ja_normalizada','linha_id',p_linha_id,'nota_final',a.nota_final);
 end if;
 select * into strict o from clube_novo.build_otimizador where id=a.build_otimizador_id;
 select * into strict b from clube_novo.build_bonificador where id=a.build_bonificador_id;
 if d.pontuacao_otimizador_bruta_evidencia is distinct from o.pontuacao
    or d.bonus_total_bonificador is distinct from b.bonus_total
    or d.otimizador_resultado_fingerprint is distinct from o.resultado_fingerprint
    or d.bonificador_resultado_fingerprint is distinct from b.resultado_fingerprint
    or d.arows_snapshot is distinct from o.arows_snapshot then
   raise exception 'normalizacao V3: resultados divergem da publicacao %',p_linha_id;
 end if;
 select round(sum((x->>1)::numeric)*4.68,1) into v_teto from jsonb_array_elements(o.arows_snapshot)x;
 v_motor:=clube_novo.normalizar_motor_v3(a.funcao_id,o.pontuacao,v_teto);
 v_final:=v_motor+b.bonus_total;
 v_normalizacao:=jsonb_build_object('versao','normalizacao-bonus-integral-20260909-v1','parametros_fingerprint','80bc2ab246b9a56dd10dd3a613056ff4d74d7b9171d4e100cc1f4caf21b36efe',
   'motor_bruto',o.pontuacao,'teto_teorico',v_teto,'fracao_teto',o.pontuacao/v_teto,
   'motor_normalizado',v_motor,'bonus_integral',b.bonus_total,'nota_final',v_final);
 v_nf:=encode(extensions.digest(convert_to(jsonb_build_object('contrato','clube-novo-normalizacao-v3',
   'linha_id',a.linha_id,'otimizador',o.resultado_fingerprint,'bonificador',b.resultado_fingerprint,
   'publicacao_v1',a.publicacao_fingerprint,'normalizacao',v_normalizacao)::text,'UTF8'),'sha256'),'hex');
 v_cf:=encode(extensions.digest(convert_to(jsonb_build_object('contrato','clube-novo-calculo-normalizacao-v3',
   'linha_id',a.linha_id,'normalizacao',v_normalizacao,'arows_snapshot',o.arows_snapshot,
   'atributos_internos',coalesce(o.atributos_internos,o.atributos_finais))::text,'UTF8'),'sha256'),'hex');
 v_lf:=encode(extensions.digest(convert_to(jsonb_build_object('contrato','clube-novo-pontuacao-final-v2',
   'linha_id',a.linha_id,'calculo_banco_fingerprint',v_cf,'bonificador_resultado_fingerprint',b.resultado_fingerprint,
   'overall_final',v_final,'publicacao_fingerprint_v1',a.publicacao_fingerprint)::text,'UTF8'),'sha256'),'hex');
 v_pf:=encode(extensions.digest(convert_to(jsonb_build_object('contrato','clube-novo-publicacao-automatica-por-linha-v1',
   'linha_id',a.linha_id,'publicacao_linha_fingerprint_v2',v_lf)::text,'UTF8'),'sha256'),'hex');
 v_prov:=jsonb_set(d.proveniencia,'{otimizador,pontuacao_normalizada}',to_jsonb(v_motor))
   ||jsonb_build_object('normalizacao',v_normalizacao,'calculo_banco_fingerprint',v_cf,
     'pontuacao_final_oficial',v_final,'publicacao_v2',v_lf);
 if l.build_otimizador_id=a.build_otimizador_id and l.build_bonificador_id=a.build_bonificador_id
    and l.nota_otimizador_resultado_fingerprint=o.resultado_fingerprint
    and l.nota_bonificador_resultado_fingerprint=b.resultado_fingerprint then
   v_linha:=jsonb_build_object('nota_numerador',l.nota_numerador,'nota_denominador',l.nota_denominador,
     'nota_do_motor',l.nota_do_motor,'nota_final',l.nota_final,'nota_normalizacao_fingerprint',l.nota_normalizacao_fingerprint,
     'nota_calculo_fingerprint',l.nota_calculo_fingerprint,'nota_calculada_em',l.nota_calculada_em,'atualizado_em',l.atualizado_em);
 end if;
 insert into clube_novo.normalizacao_publicacao_historico_v3(regua_versao,linha_id,build_otimizador_id,build_bonificador_id,
   publicacao_anterior_fingerprint,ativa_anterior,delta_anterior,linha_nota_anterior,motor_normalizado_novo,nota_final_nova)
 values('normalizacao-bonus-integral-20260909-v1',a.linha_id,o.id,b.id,a.publicacao_v2_fingerprint,
   jsonb_build_object('nota_final',a.nota_final,'publicacao_v2_fingerprint',a.publicacao_v2_fingerprint,
     'proveniencia',a.proveniencia,'versao_publicacao',a.versao_publicacao,'atualizado_em',a.atualizado_em),
   jsonb_build_object('pontuacao_otimizador_normalizada',d.pontuacao_otimizador_normalizada,'overall_final',d.overall_final,
     'normalizacao_fingerprint',d.normalizacao_fingerprint,'calculo_banco_fingerprint',d.calculo_banco_fingerprint,
     'publicacao_linha_fingerprint_v2',d.publicacao_linha_fingerprint_v2,'publicacao_v2_fingerprint',d.publicacao_v2_fingerprint,
     'proveniencia',d.proveniencia),v_linha,v_motor,v_final)
 on conflict(regua_versao,linha_id,publicacao_anterior_fingerprint) do nothing;
 update clube_novo.build_pontuacao_final_v2_delta_v1 set pontuacao_otimizador_normalizada=v_motor,overall_final=v_final,
   normalizacao_fingerprint=v_nf,calculo_banco_fingerprint=v_cf,publicacao_linha_fingerprint_v2=v_lf,
   publicacao_v2_fingerprint=v_pf,proveniencia=v_prov
 where publicacao_v2_fingerprint=d.publicacao_v2_fingerprint and linha_id=a.linha_id;
 get diagnostics v_qtd=row_count;
 if v_qtd<>1 then raise exception 'normalizacao V3: delta alterado concorrentemente';end if;
 update clube_novo.build_publicacao_linha_ativa_v1 set nota_final=v_final,publicacao_v2_fingerprint=v_pf,
   proveniencia=v_prov,versao_publicacao=versao_publicacao+1,atualizado_em=v_agora where linha_id=a.linha_id;
 if v_linha is not null then
   update clube_novo.build_linha_card set nota_numerador=o.pontuacao,nota_denominador=v_teto,
    nota_do_motor=v_motor,nota_final=v_final,nota_normalizacao_fingerprint=v_nf,nota_calculo_fingerprint=v_cf,
    nota_calculada_em=v_agora where id=a.linha_id;
 end if;
 if not exists(select 1 from clube_novo.build_publicacao_linha_ativa_v1 ax
     join clube_novo.build_pontuacao_final_v2_delta_v1 dx on dx.linha_id=ax.linha_id
     and dx.publicacao_v2_fingerprint=ax.publicacao_v2_fingerprint
     where ax.linha_id=a.linha_id and ax.nota_final=v_final and dx.overall_final=v_final
       and dx.pontuacao_otimizador_normalizada=v_motor and dx.bonus_total_bonificador=b.bonus_total) then
   raise exception 'normalizacao V3: readback divergiu';
 end if;
 return jsonb_build_object('estado','normalizada','linha_id',a.linha_id,'nota_final',v_final,
   'motor_normalizado',v_motor,'bonus_integral',b.bonus_total,'normalizacao_versao','normalizacao-bonus-integral-20260909-v1');
end $fn$;
revoke all on function clube_novo.normalizar_publicacao_v3(bigint) from public,anon,authenticated;
grant execute on function clube_novo.normalizar_publicacao_v3(bigint) to service_role;

create function clube_novo.normalizar_publicacoes_pendentes_v3(p_limite integer default 200)
returns jsonb language plpgsql security definer set search_path='' as $fn$
declare x record;r jsonb;n integer:=0;
begin
 if p_limite<1 or p_limite>1000 then raise exception 'limite entre 1 e 1000';end if;
 for x in select a.linha_id from clube_novo.build_publicacao_linha_ativa_v1 a
   join clube_novo.build_linha_card l on l.id=a.linha_id
   where a.proveniencia#>>'{normalizacao,versao}' is distinct from 'normalizacao-bonus-integral-20260909-v1'
   order by a.linha_id limit p_limite for update of l skip locked loop
   r:=clube_novo.normalizar_publicacao_v3(x.linha_id);n:=n+1;
 end loop;
 return jsonb_build_object('normalizadas',n,'regua','normalizacao-bonus-integral-20260909-v1');
end $fn$;
revoke all on function clube_novo.normalizar_publicacoes_pendentes_v3(integer) from public,anon,authenticated;
grant execute on function clube_novo.normalizar_publicacoes_pendentes_v3(integer) to service_role;
