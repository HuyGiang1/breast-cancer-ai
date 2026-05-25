/* ================================================================
   BreastCare Mint — app.js v2
   Fixes: missing IDs, navigation bug, history detail view
   New:   Stats page, About page, toast system, mobile nav
   ================================================================ */

const IS_LOCAL_STATIC_FRONTEND = ['8080', '5500', '4173', '3000'].includes(window.location.port);
const API_HOST = window.location.hostname || '127.0.0.1';
const BACKEND_ORIGIN = IS_LOCAL_STATIC_FRONTEND
    ? `${window.location.protocol}//${API_HOST}:8000`
    : window.location.origin;
const API_BASE_URL = `${BACKEND_ORIGIN}/api/v1`;

// ── State ──────────────────────────────────────────────────────
const state = {
    authToken:    localStorage.getItem('bcai_token') || '',
    currentUser:  (() => { try { return JSON.parse(localStorage.getItem('bcai_user') || 'null'); } catch { return null; } })(),
    patients:     [],
    history:      [],
    patientHistory: [],
    doctorPatientHistory: [],
    mlModels:     [],
    dlModels:     [],
    benchmarks:   {},
    currentPage:  'home',
    currentPredictTab: 'ml',
    selectedDlImageFile: null,
    fusionClinicalData: null,
    selectedFusionImageFile: null,
    predictionCount: 0,
    editingPatientId: null,
    chatTurns: [],
};

// ── Features list ──────────────────────────────────────────────
const FEATURES = [
    'mean_radius','mean_texture','mean_perimeter','mean_area','mean_smoothness',
    'mean_compactness','mean_concavity','mean_concave_points','mean_symmetry','mean_fractal_dimension',
    'radius_error','texture_error','perimeter_error','area_error','smoothness_error',
    'compactness_error','concavity_error','concave_points_error','symmetry_error','fractal_dimension_error',
    'worst_radius','worst_texture','worst_perimeter','worst_area','worst_smoothness',
    'worst_compactness','worst_concavity','worst_concave_points','worst_symmetry','worst_fractal_dimension',
];

const SAMPLES = {
    benign: {
        mean_radius:13.54,mean_texture:14.36,mean_perimeter:87.46,mean_area:566.3,
        mean_smoothness:0.09779,mean_compactness:0.08129,mean_concavity:0.06664,
        mean_concave_points:0.04781,mean_symmetry:0.1885,mean_fractal_dimension:0.05766,
        radius_error:0.2699,texture_error:0.7886,perimeter_error:2.058,area_error:23.56,
        smoothness_error:0.008462,compactness_error:0.0146,concavity_error:0.02387,
        concave_points_error:0.01315,symmetry_error:0.0198,fractal_dimension_error:0.0023,
        worst_radius:15.11,worst_texture:19.26,worst_perimeter:99.7,worst_area:711.2,
        worst_smoothness:0.144,worst_compactness:0.1773,worst_concavity:0.239,
        worst_concave_points:0.1288,worst_symmetry:0.2977,worst_fractal_dimension:0.07259,
    },
    malignant: {
        mean_radius:17.99,mean_texture:10.38,mean_perimeter:122.8,mean_area:1001.0,
        mean_smoothness:0.1184,mean_compactness:0.2776,mean_concavity:0.3001,
        mean_concave_points:0.1471,mean_symmetry:0.2419,mean_fractal_dimension:0.07871,
        radius_error:1.095,texture_error:0.9053,perimeter_error:8.589,area_error:153.4,
        smoothness_error:0.006399,compactness_error:0.04904,concavity_error:0.05373,
        concave_points_error:0.01587,symmetry_error:0.03003,fractal_dimension_error:0.006193,
        worst_radius:25.38,worst_texture:17.33,worst_perimeter:184.6,worst_area:2019.0,
        worst_smoothness:0.1622,worst_compactness:0.6656,worst_concavity:0.7119,
        worst_concave_points:0.2654,worst_symmetry:0.4601,worst_fractal_dimension:0.1189,
    },
};

// ── Static content data ────────────────────────────────────────
const HOME_HIGHLIGHTS = [
    { tag:'Cảnh báo sớm', title:'Không nên xem nhẹ những thay đổi ở vú', text:'Khối cứng, thay đổi da, núm vú tụt mới xuất hiện hoặc tiết dịch bất thường đều là lý do cần đi khám sớm.' },
    { tag:'Theo dõi đúng', title:'Người dùng cần biết mình đang đối mặt điều gì', text:'Trang kiến thức và chăm sóc được làm để người bệnh và gia đình hiểu rõ dấu hiệu, ăn uống và phục hồi sau điều trị.' },
    { tag:'Sàng lọc hỗ trợ', title:'Dự đoán là bước hỗ trợ — không phải kết luận', text:'Khu AI giúp người dùng có thêm lớp tham khảo, nhưng kết luận cuối phải đến từ bác sĩ và xét nghiệm cần thiết.' },
];

const LEARN_ITEMS = [
    { title:'Hiểu đúng về sàng lọc ung thư vú', text:'Sàng lọc là phát hiện sớm nguy cơ ngay khi triệu chứng chưa rõ. Nhũ ảnh, siêu âm và khám lâm sàng thường mở đầu. Nếu có nghi ngờ cao, bác sĩ chỉ định thêm sinh thiết hoặc giải phẫu bệnh để chẩn đoán xác định.' },
    { title:'Chuẩn bị trước buổi khám', text:'Người bệnh nên ghi rõ thời gian phát hiện bất thường, khối có lớn nhanh không, có đau hay tiết dịch không, tiền sử gia đình có ai mắc ung thư vú hoặc buồng trứng không. Nếu đã chụp trước thì mang phim và kết quả cũ.' },
    { title:'Dấu hiệu cần đi khám sớm', text:'Sờ thấy khối cứng ở vú hoặc nách, thay đổi da kiểu lõm, co kéo, sần vỏ cam, núm vú tụt mới xuất hiện, tiết dịch bất thường và đau khu trú kéo dài. Không phải mọi khối đều ác tính, nhưng cần khám để làm rõ.' },
    { title:'Hiểu đúng kết quả AI', text:'Kết quả AI là tín hiệu hỗ trợ sàng lọc. Nó giúp người dùng hình dung nguy cơ và sắp xếp bước đi tiếp theo, nhưng không thay thế bác sĩ, chẩn đoán hình ảnh chuyên sâu hoặc giải phẫu bệnh.' },
    { title:'Phục hồi và hỗ trợ tinh thần', text:'Ngoài điều trị, người bệnh cần hỗ trợ ăn uống, ngủ nghỉ, vận động nhẹ và tinh thần. Một cuốn sổ ghi triệu chứng, lịch thuốc và câu hỏi cho bác sĩ giúp quá trình điều trị bớt rối hơn nhiều.' },
    { title:'Nên hỏi gì sau kết quả bất thường', text:'Hỏi rõ: mức độ nghi ngờ hiện tại là bao nhiêu, xét nghiệm tiếp theo là gì, có cần sinh thiết không, khi nào tái khám, và dấu hiệu nào cần quay lại ngay.' },
];

const LEARN_DEEP = [
    { title:'Việc nên làm ngay sau khi thấy bất thường', text:'Điều quan trọng nhất không phải tự suy đoán lâu mà là lên lịch đi khám. Trong lúc chờ, ghi lại cảm giác đau, vị trí, kích thước ước lượng, thời gian phát hiện, có tiết dịch và thay đổi da không.' },
    { title:'Ăn uống trong giai đoạn điều trị', text:'Mục tiêu thường không phải kiêng nhiều mà là giữ được thể trạng. Ưu tiên đủ nước, đủ đạm, rau xanh, trái cây chín, ngũ cốc nguyên hạt và chia nhỏ bữa nếu mệt. Chế độ ăn cực đoan có thể làm tụt sức.' },
    { title:'Kết quả dự đoán nên được hiểu như thế nào', text:'Phần trăm trên web giúp hình dung mức nghi ngờ tương đối. Kết quả càng cao thì càng nên đi khám sớm, nhưng dù kết quả thấp mà triệu chứng rõ thì vẫn cần kiểm tra y khoa.' },
    { title:'Vai trò của người thân trong chăm sóc', text:'Nhắc lịch tái khám, ghi lại phản ứng sau điều trị, chuẩn bị bữa ăn dễ dùng và đồng hành trong các buổi tư vấn — một người đi cùng biết rõ hồ sơ bệnh giúp trao đổi với bác sĩ đầy đủ hơn nhiều.' },
];

const FAQ_ITEMS = [
    { q:'AI điểm cao có tự chẩn đoán ung thư được không?', a:'Không. Đây là lớp hỗ trợ sàng lọc. Chẩn đoán cuối cùng cần bác sĩ đánh giá và khi cần thì có sinh thiết hoặc giải phẫu bệnh.' },
    { q:'Có cần tạo hồ sơ bệnh nhân trước không?', a:'Nếu chỉ test nhanh thì dùng chế độ khách. Còn để sử dụng thật và lưu lịch sử, nên đăng nhập và tạo hồ sơ bệnh nhân để theo dõi dễ hơn.' },
    { q:'Nếu model ảnh cho kết quả chưa chắc thì sao?', a:'Dùng thêm kết quả lâm sàng như tín hiệu hỗ trợ, sau đó chuyển sang bác sĩ đánh giá thay vì xem kết quả ảnh là kết luận cuối.' },
    { q:'Các trang kiến thức có thay thế tư vấn y khoa không?', a:'Không. Chúng được thiết kế để hỗ trợ người bệnh chuẩn bị tốt hơn cho buổi khám và quá trình trao đổi với bác sĩ.' },
    { q:'Lịch sử dự đoán được lưu ở đâu?', a:'Lịch sử được lưu trên server sau khi đăng nhập. Mỗi dự đoán ML, DL và kết hợp đều được lưu tự động. Bác sĩ có thể gắn lịch sử theo từng hồ sơ bệnh nhân.' },
];

const VIDEO_ITEMS = [
    { tag:'Khái quát', title:'Tổng quan về ung thư vú', text:'Video mở đầu để người dùng có cái nhìn tổng quát về bệnh, cách hiểu nguy cơ và hướng xử lý ban đầu.', embed:'https://www.youtube.com/embed/xxK85MDdMNE', link:'https://www.youtube.com/watch?v=xxK85MDdMNE' },
    { tag:'Chụp nhũ ảnh', title:'Chuẩn bị trước khi chụp nhũ ảnh', text:'Giúp người xem hình dung trước quá trình chụp và những điều nên chuẩn bị để bớt lo lắng.', embed:'https://www.youtube.com/embed/mCmJQGpjGNA', link:'https://www.youtube.com/watch?v=mCmJQGpjGNA' },
    { tag:'Tự theo dõi', title:'Tự kiểm tra và nhận biết dấu hiệu bất thường', text:'Phù hợp cho người dùng cần xem lại các thay đổi nên theo dõi tại nhà trước khi đi khám.', embed:'https://www.youtube.com/embed/t4COaz2a_OE', link:'https://www.youtube.com/watch?v=t4COaz2a_OE' },
    { tag:'Dinh dưỡng', title:'Dinh dưỡng và phục hồi sau điều trị', text:'Nội dung về ăn uống, nước, đạm và cách giữ thể trạng ổn định trong giai đoạn điều trị hoặc hồi phục.', embed:'https://www.youtube.com/embed/vZ-UDV6pkyg', link:'https://www.youtube.com/watch?v=vZ-UDV6pkyg' },
    { tag:'Phục hồi', title:'Bài tập nhẹ cho phục hồi và phù bạch huyết', text:'Bài tập nhẹ cho người có nguy cơ hoặc đang gặp phù bạch huyết sau điều trị. Chỉ tập khi bác sĩ cho phép.', embed:'https://www.youtube.com/embed/SXHbGUFW8Io', link:'https://www.youtube.com/watch?v=SXHbGUFW8Io' },
    { tag:'Dấu hiệu', title:'Understanding Breast Cancer (Symptoms & Treatment)', text:'Giải thích khá dễ hiểu về triệu chứng, yếu tố nguy cơ, xét nghiệm và điều trị để người dùng có nền tảng ban đầu.', embed:'https://www.youtube.com/embed/xxK85MDdMNE', link:'https://www.youtube.com/watch?v=xxK85MDdMNE' },
];

const PRODUCT_ITEMS = [
    { tag:'Thoải mái', title:'Áo ngực mở phía trước cho giai đoạn hồi phục', text:'Phù hợp sau can thiệp, dễ mặc hơn và giảm kéo căng khi cử động tay.' },
    { tag:'Da liễu', title:'Kem dưỡng dịu nhẹ cho da nhạy cảm', text:'Hỗ trợ da khô hoặc kích ứng trong giai đoạn điều trị khi sản phẩm hương liệu mạnh gây khó chịu.' },
    { tag:'Theo dõi', title:'Sổ theo dõi sức khỏe hoặc nhật ký triệu chứng', text:'Giúp ghi lại khó chịu, tác dụng thuốc, lịch chụp và câu hỏi cho lần khám tiếp theo.' },
    { tag:'Nghỉ ngơi', title:'Gối kê hỗ trợ khi nằm nghỉ', text:'Một vật dụng đơn giản có thể giúp người bệnh thấy dễ chịu hơn sau thủ thuật hoặc khi vùng ngực còn đau.' },
    { tag:'Dinh dưỡng', title:'Kế hoạch bữa ăn ưu tiên đạm', text:'Một thực đơn có cấu trúc thường thực tế hơn chỉ dùng thực phẩm bổ sung khi người bệnh mệt và ăn kém.' },
    { tag:'Vận động', title:'Dây kháng lực nhẹ', text:'Chỉ nên dùng khi bác sĩ cho phép, đặc biệt trong giai đoạn tập phục hồi biên độ vận động sau điều trị.' },
];

const ACCOUNT_CHECKLIST = [
    'Nên tạo tài khoản trước khi sử dụng thật để có thể lưu lịch sử dự đoán.',
    'Nếu dùng tài khoản bác sĩ, mỗi bệnh nhân nên có một hồ sơ riêng để kết quả lâm sàng, ảnh và kết hợp được theo dõi đúng.',
    'Nếu quên mật khẩu, backend có luồng tạo reset token để khôi phục tài khoản.',
    'Chế độ khách vẫn có thể dùng để thử nhanh khu dự đoán mà không cần lưu dữ liệu.',
];

const CHAT_SUGGESTIONS = [
    'Tôi sờ thấy khối cứng ở vú thì nên làm gì tiếp theo?',
    'Dấu hiệu nào của ung thư vú cần đi khám sớm?',
    'Người nghi ngờ ung thư vú nên ăn gì và kiêng gì?',
    'Chụp nhũ ảnh có vai trò gì trong sàng lọc ung thư vú?',
    'Sau điều trị ung thư vú nên theo dõi những gì?',
];

const CARE_BEFORE = [
    'Đi khám chuyên khoa sớm nếu có khối cứng, thay đổi da, tiết dịch đầu ti hoặc đau khu trú kéo dài.',
    'Chuẩn bị hồ sơ cũ, phim chụp trước đó, danh sách thuốc và tiền sử gia đình trước buổi khám.',
    'Ăn đủ đạm, rau xanh và ngủ đủ để cơ thể có nền thể trạng tốt trước khi làm thêm xét nghiệm hoặc điều trị.',
    'Không tự ý bỏ khám để chạy theo các phương pháp truyền miệng thiếu kiểm chứng.',
];

const CARE_AFTER = [
    'Ưu tiên bữa ăn dễ tiêu, giàu đạm và chia nhỏ nếu mệt hoặc buồn nôn trong giai đoạn điều trị.',
    'Theo dõi cân nặng, mức ăn uống, đau, mệt, phù tay và các thay đổi bất thường để báo lại cho bác sĩ.',
    'Duy trì vận động nhẹ, giấc ngủ đều và hỗ trợ tinh thần từ gia đình hoặc nhóm chăm sóc.',
    'Giữ lịch tái khám và không bỏ qua những mốc xét nghiệm hoặc chụp kiểm tra sau điều trị.',
];

const CARE_FOODS = [
    { title:'Rau họ cải', text:'Bông cải xanh, súp lơ, cải bắp là nhóm thường được nhắc tới trong các bài viết dinh dưỡng hỗ trợ vì giàu chất xơ và vi chất.' },
    { title:'Cá giàu omega-3', text:'Cá hồi và các nguồn chất béo tốt thường được khuyến khích để cân bằng khẩu phần và hỗ trợ sức khỏe toàn thân.' },
    { title:'Trái cây chín và rau xanh', text:'Nguồn vitamin, khoáng chất và chất xơ giúp bữa ăn đa dạng hơn, đặc biệt khi người bệnh ăn uống kém.' },
    { title:'Đạm nạc và họ đậu', text:'Thịt nạc, trứng, sữa, tôm, đậu và các nguồn đạm là nền quan trọng để duy trì thể trạng trong điều trị.' },
];

const CARE_AVOID = [
    'Hạn chế rượu bia và đồ uống nhiều đường.',
    'Giảm thịt chế biến sẵn, món chiên rán nhiều dầu và thức ăn quá mặn.',
    'Không lạm dụng thực phẩm bổ sung hoặc chế độ kiêng cực đoan làm tụt thể trạng.',
    'Tránh bỏ bữa kéo dài vì điều này có thể làm người bệnh suy kiệt nhanh hơn trong điều trị.',
];

const CARE_SOURCES = [
    { label:'MEDLATEC - Top 8 thực phẩm nên ăn', url:'https://w1.medlatec.vn/tin-tuc/an-gi-de-ngan-ngua-ung-thu-vu-dung-bo-qua-top-8-cac-thuc-pham-sau-s0-n22875' },
    { label:'Tâm Anh - Ung thư vú nên ăn gì và kiêng gì', url:'https://tamanhhospital.vn/ung-thu-vu-nen-an-gi-va-kieng-gi/' },
    { label:'Bệnh viện K - Thực phẩm tốt cho người bệnh ung thư vú', url:'https://benhvienk.vn/top-10-thuc-pham-tot-cho-nguoi-benh-ung-thu-vu-nd93109.html' },
    { label:'Vinmec - Dinh dưỡng hỗ trợ bệnh nhân điều trị ung thư vú', url:'https://www.vinmec.com/vie/bai-viet/dinh-duong-ho-tro-benh-nhan-dieu-tri-ung-thu-vu-vi' },
];

const CARE_IMAGES = [
    { title:'Bữa ăn cân bằng', text:'Minh họa khẩu phần ưu tiên rau, trái cây, đạm nạc và ngũ cốc nguyên hạt.', src:'assets/image/anh-avar-1632575744465751354437-0-0-445-712-crop-16325757580671986263760.webp' },
    { title:'Tự theo dõi thay đổi', text:'Nhắc người dùng chú ý các thay đổi bất thường và đi khám sớm khi cần.', src:'assets/image/ung-thu-vu-co-di-truyen-khong.jpg' },
    { title:'Trao đổi với bác sĩ', text:'Ưu tiên kiểm tra chuyên khoa, tái khám đều và hỏi kỹ trước khi đổi chế độ ăn hay vận động.', src:'assets/image/1639013521.jpg' },
    { title:'Theo dõi cơn đau và thay đổi ở vú', text:'Không bỏ qua những thay đổi như đau khu trú, da lõm hay căng tức kéo dài.', src:'assets/image/tuc-gian-ung-thu-vu1.jpg' },
    { title:'Thực phẩm ưu tiên mỗi ngày', text:'Rau xanh, trái cây chín, nguồn đạm nạc và nước nên là phần ổn định trong bữa ăn hằng ngày.', src:'assets/image/medium_20190430_164642_894592_shutterstock_612082_max_1800x1800_jpg_a9f38bf039.jpg' },
    { title:'Nghỉ ngơi và phục hồi', text:'Giấc ngủ, vận động nhẹ và nhịp sinh hoạt ổn định giúp người bệnh hồi phục bền hơn.', src:'assets/image/3(45).jpg' },
];

const PRODUCT_WARNINGS = [
    'Không xem thực phẩm chức năng hay sản phẩm hỗ trợ là cách thay thế cho phác đồ điều trị chính thống.',
    'Nếu đang hóa trị, xạ trị hoặc vừa phẫu thuật, mọi thay đổi lớn về ăn uống hay vận động nên hỏi bác sĩ trước.',
    'Các sản phẩm hỗ trợ chỉ có giá trị khi đi kèm tái khám đều và theo dõi triệu chứng cẩn thận.',
];

const STATS_DISCLAIMERS = [
    'Kết quả AI chỉ mang tính chất tham khảo và hỗ trợ sàng lọc ban đầu.',
    'Độ chính xác được đo trên tập test tiêu chuẩn (Wisconsin WDBC) — hiệu suất thực tế có thể khác nhau tùy dữ liệu đầu vào.',
    'Model DL được huấn luyện trên ảnh nhũ ảnh đặc thù — ảnh không đúng định dạng có thể cho kết quả không đáng tin cậy.',
    'Mọi quyết định y tế cần dựa trên chẩn đoán của bác sĩ chuyên khoa và xét nghiệm chính thức.',
];

const ABOUT_ML_LIST = [
    'Logistic Regression — nền tảng y khoa, giải thích rõ ràng với hệ số SHAP.',
    'Random Forest — ensemble method, chống overfitting tốt trên dữ liệu lâm sàng.',
    'XGBoost — gradient boosting, đạt độ chính xác cao nhất (~98%) trên Wisconsin WDBC.',
];

const ABOUT_DL_LIST = [
    'Custom CNN — mô hình DL đang hoạt động hiện tại cho phân tích ảnh nhũ ảnh trên website.',
    'Grad-CAM / heatmap — lớp giải thích vùng ảnh mà hệ thống chú ý khi tạo dự đoán.',
    'ResNet50 và EfficientNet-B0 — các hướng thử nghiệm trước đó, hiện không dùng trong luồng dự đoán chính.',
    'Mục tiêu hiện tại là giữ một pipeline DL ổn định, dễ kiểm soát và nhất quán với phần thống kê thực tế.',
];

const DL_RESEARCH_BENCHMARKS = [
    {
        name: 'EfficientNet-B0',
        variant: 'Baseline transfer learning',
        accuracy: 0.419689,
        sensitivity: 1.0,
        specificity: 0.0,
        roc_auc: 0.5,
        decision: 'Không chọn làm model chính vì gần như nghiêng hẳn về một phía trên tập đánh giá.',
    },
    {
        name: 'ResNet50',
        variant: 'Baseline transfer learning',
        accuracy: 0.458549,
        sensitivity: 0.956790,
        specificity: 0.098214,
        roc_auc: 0.546737,
        decision: 'Có học được tín hiệu ảnh nhưng độ đặc hiệu thấp, dễ báo động quá mức.',
    },
    {
        name: 'Custom CNN',
        variant: 'Baseline',
        accuracy: 0.476684,
        sensitivity: 0.956790,
        specificity: 0.129464,
        roc_auc: 0.604608,
        decision: 'Tốt hơn hai baseline còn lại và dễ kiểm soát hơn trong pipeline hiện tại.',
    },
    {
        name: 'Custom CNN v2',
        variant: 'ROI-tuned / fine-tuned',
        accuracy: 0.505181,
        sensitivity: 0.950617,
        specificity: 0.183036,
        roc_auc: 0.583636,
        decision: 'Là hướng CNN được giữ lại để triển khai vì cân bằng tốt hơn giữa hiệu suất và khả năng vận hành.',
    },
];

const DL_DEMO_IMAGES = {
    benign: {
        path: 'assets/demo-images/demo-benign-mammogram.png',
        filename: 'demo-benign-mammogram.png',
        label: 'Ảnh mẫu lành tính',
    },
    malignant: {
        path: 'assets/demo-images/demo-malignant-mammogram.png',
        filename: 'demo-malignant-mammogram.png',
        label: 'Ảnh mẫu nghi ngờ ác tính',
    },
};

// ================================================================
// UTILITY FUNCTIONS
// ================================================================

function el(id) { return document.getElementById(id); }

function setText(id, value) {
    const e = el(id);
    if (e) e.textContent = value;
}

function formatFeatureLabel(name) {
    return name.split('_').map(p => p.charAt(0).toUpperCase() + p.slice(1)).join(' ');
}

function formatPercent(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A';
    return `${(Number(value) * 100).toFixed(1)}%`;
}

function initialsFromName(name) {
    const parts = String(name || 'K').trim().split(/\s+/).filter(Boolean).slice(0, 2);
    return (parts.map(p => p.charAt(0).toUpperCase()).join('') || 'K').slice(0, 2);
}

function translateDiagnosis(value) {
    if (value === 'Malignant') return 'Nghi ngờ ác tính';
    if (value === 'Benign') return 'Nghiêng lành tính';
    return value || 'Chưa rõ';
}

function translateRiskBand(value) {
    if (value === 'High')   return 'Cao';
    if (value === 'Medium') return 'Trung bình';
    if (value === 'Low')    return 'Thấp';
    return value || 'Chưa rõ';
}

function cleanNarrative(text) {
    return String(text || '')
        .replace(/[*_`#>-]/g, '')
        .replace(/\n{3,}/g, '\n\n')
        .trim();
}

function badgeClass(diagnosis, riskBand) {
    if (diagnosis === 'Malignant') return 'malignant';
    if (riskBand   === 'Medium')   return 'medium';
    return 'benign';
}

function resolveExplanationImage(src) {
    if (!src) return null;
    if (src.startsWith('data:image')) return src;
    if (src.startsWith('http://') || src.startsWith('https://')) return src;
    if (src.startsWith('/results/')) return `${BACKEND_ORIGIN}${src}`;
    if (src.startsWith('/')) return `${BACKEND_ORIGIN}${src}`;
    return `${BACKEND_ORIGIN}/${src.replace(/^\/+/, '')}`;
}

function selectedPatientId() {
    const s = el('patientSelect');
    return s && s.value ? Number(s.value) : null;
}

function selectedPredictionPatientId() {
    const s = el('predictionPatientSelect');
    return s && s.value ? Number(s.value) : null;
}

function selectedHistoryPatientId() {
    const s = el('historyPatientSelect');
    return s && s.value ? Number(s.value) : null;
}

function clearPredictionResult() {
    const resultCard = el('resultCard');
    const content = el('resultContent');
    if (resultCard) resultCard.style.display = 'block';
    if (content) {
        content.className = 'result-empty';
        content.innerHTML = 'Chưa có kết quả dự đoán. Hãy điền dữ liệu và nhấn chạy dự đoán.';
    }
    setStatus('predictionStatus', 'Sẵn sàng dự đoán.', 'muted');
}

function countFilledClinicalInputs() {
    return FEATURES.reduce((count, feature) => {
        const input = el(`feature-${feature}`);
        return input && input.value.trim() ? count + 1 : count;
    }, 0);
}

function countFilledFusionClinicalInputs() {
    if (!state.fusionClinicalData) return 0;
    return FEATURES.reduce((count, feature) => {
        const value = state.fusionClinicalData?.[feature];
        return (value !== null && value !== undefined && !Number.isNaN(Number(value))) ? count + 1 : count;
    }, 0);
}

function updateMultimodalPanel() {
    const filled = countFilledFusionClinicalInputs();
    const hasImage = !!state.selectedFusionImageFile;
    const clinicalStatus = el('fusionClinicalStatus');
    const imageStatus = el('fusionImageStatus');
    const preview = el('fusionImagePreview');
    const previewEmpty = el('fusionImagePreviewEmpty');
    const predictBtn = el('predictFusionBtn');

    if (clinicalStatus) {
        clinicalStatus.textContent = filled === FEATURES.length
            ? `Đã sẵn sàng ${filled}/30 chỉ số lâm sàng cho nhánh ML.`
            : `Hiện có ${filled}/30 chỉ số. Cần đủ 30 chỉ số để chạy dự đoán kết hợp.`;
    }

    if (imageStatus) {
        imageStatus.textContent = hasImage
            ? `Đã chọn ảnh: ${state.selectedFusionImageFile.name}`
            : 'Chưa có ảnh nhũ ảnh được chọn cho nhánh DL.';
    }

    if (preview && previewEmpty) {
        if (hasImage) {
            preview.style.display = 'block';
            previewEmpty.style.display = 'none';
        } else {
            preview.removeAttribute('src');
            preview.style.display = 'none';
            previewEmpty.style.display = 'block';
        }
    }

    if (predictBtn) predictBtn.disabled = !(filled === FEATURES.length && hasImage);
}

function resetPredictionWorkspace() {
    FEATURES.forEach((feature) => {
        const input = el(`feature-${feature}`);
        if (input) input.value = '';
    });

    const csvInput = el('csvInput');
    if (csvInput) csvInput.value = '';
    const reportImageInput = el('reportImageInput');
    if (reportImageInput) reportImageInput.value = '';
    const fusionCsvInput = el('fusionCsvInput');
    if (fusionCsvInput) fusionCsvInput.value = '';
    const fusionReportImageInput = el('fusionReportImageInput');
    if (fusionReportImageInput) fusionReportImageInput.value = '';

    state.selectedDlImageFile = null;
    const imageInput = el('imageInput');
    if (imageInput) imageInput.value = '';

    const imagePreview = el('imagePreview');
    if (imagePreview) imagePreview.removeAttribute('src');

    const uploadShell = imagePreview?.closest('.upload-shell');
    uploadShell?.classList.remove('has-image');

    const predictDlBtn = el('predictDlBtn');
    if (predictDlBtn) predictDlBtn.disabled = true;

    state.fusionClinicalData = null;
    state.selectedFusionImageFile = null;
    const fusionImageInput = el('fusionImageInput');
    if (fusionImageInput) fusionImageInput.value = '';
    const fusionImagePreview = el('fusionImagePreview');
    if (fusionImagePreview) fusionImagePreview.removeAttribute('src');
    fusionImagePreview?.closest('.upload-shell')?.classList.remove('has-image');

    ['patientSelect', 'predictionPatientSelect', 'historyPatientSelect'].forEach((id) => {
        const select = el(id);
        if (select) select.value = '';
    });

    clearPredictionResult();
    updateMultimodalPanel();
}

function persistGuestChat() {
    if (state.currentUser) return;
    localStorage.setItem('bcai_guest_chat', JSON.stringify(state.chatTurns));
}

function loadGuestChat() {
    if (state.currentUser) return;
    try {
        state.chatTurns = JSON.parse(localStorage.getItem('bcai_guest_chat') || '[]');
    } catch {
        state.chatTurns = [];
    }
}

function setSelectedDlImage(file, previewSrc, message) {
    state.selectedDlImageFile = file;
    const preview = el('imagePreview');
    if (preview) {
        const shell = preview.closest('.upload-shell');
        preview.src = previewSrc;
        shell?.classList.add('has-image');
    }
    if (el('predictDlBtn')) el('predictDlBtn').disabled = false;
    if (message) showToast(message, 'success');
}

function setSelectedFusionImage(file, previewSrc, message) {
    state.selectedFusionImageFile = file;
    const preview = el('fusionImagePreview');
    if (preview) {
        const shell = preview.closest('.upload-shell');
        preview.src = previewSrc;
        shell?.classList.add('has-image');
    }
    updateMultimodalPanel();
    if (message) showToast(message, 'success');
}

async function loadDemoDlImage(kind) {
    const demo = DL_DEMO_IMAGES[kind];
    if (!demo) return;
    try {
        const res = await fetch(demo.path);
        if (!res.ok) throw new Error('Không tải được ảnh mẫu.');
        const blob = await res.blob();
        const file = new File([blob], demo.filename, { type: blob.type || 'image/png' });
        setSelectedDlImage(file, demo.path, `Đã nạp ${demo.label}.`);
    } catch (err) {
        showToast(err.message || 'Không tải được ảnh mẫu demo.', 'error');
    }
}

async function loadFusionDemo(kind) {
    state.fusionClinicalData = { ...SAMPLES[kind] };
    const demo = DL_DEMO_IMAGES[kind];
    if (demo) {
        try {
            const res = await fetch(demo.path);
            if (!res.ok) throw new Error('Không tải được ảnh mẫu.');
            const blob = await res.blob();
            const file = new File([blob], demo.filename, { type: blob.type || 'image/png' });
            setSelectedFusionImage(file, demo.path, `Đã nạp dữ liệu mẫu ${kind === 'benign' ? 'lành tính' : 'ác tính'} cho tab kết hợp.`);
        } catch (err) {
            showToast(err.message || 'Không tải được ảnh mẫu demo.', 'error');
        }
    }
    switchPredictTab('fusion');
    updateMultimodalPanel();
}

function renderChat() {
    const container = el('chatHistory');
    if (!container) return;
    if (!state.chatTurns.length) {
        container.innerHTML = '<div class="result-empty">Chưa có tin nhắn. Hãy bắt đầu bằng một câu hỏi về ung thư vú.</div>';
        return;
    }
    container.innerHTML = state.chatTurns.map((turn) => `
        <div class="chat-message ${turn.role === 'assistant' ? 'assistant' : 'user'}">
            <div class="chat-message-role">${turn.role === 'assistant' ? 'BreastCare Assistant' : 'Bạn'}</div>
            <div class="chat-message-body">${escapeHtml(turn.content).replace(/\n/g, '<br>')}</div>
        </div>
    `).join('');
    container.scrollTop = container.scrollHeight;
}

async function loadChatHistory() {
    if (!state.currentUser) {
        loadGuestChat();
        renderChat();
        return;
    }
    try {
        const res = await apiFetch(`${API_BASE_URL}/chat/history/`);
        if (!res.ok) throw new Error('Không tải được lịch sử chat');
        const rows = await res.json();
        state.chatTurns = [];
        rows.reverse().forEach((row) => {
            state.chatTurns.push({ role: 'user', content: row.question });
            state.chatTurns.push({ role: 'assistant', content: row.answer });
        });
    } catch {
        state.chatTurns = [];
    }
    renderChat();
}

async function sendChatMessage(prefilledMessage = '') {
    const input = el('chatMessageInput');
    const message = (prefilledMessage || input?.value || '').trim();
    if (!message) return;

    state.chatTurns.push({ role: 'user', content: message });
    renderChat();
    if (input) input.value = '';
    setText('chatStatus', 'Đang soạn câu trả lời...');
    persistGuestChat();

    try {
        const recentHistory = state.chatTurns.slice(-10).map((turn) => ({
            role: turn.role,
            content: turn.content,
        }));
        const res = await apiFetch(`${API_BASE_URL}/chat/ask/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, history: recentHistory }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Chatbot không phản hồi được');
        state.chatTurns.push({ role: 'assistant', content: data.answer });
        setText('chatStatus', `Đã trả lời bằng ${data.provider}.`);
        persistGuestChat();
        renderChat();
    } catch (err) {
        state.chatTurns.push({ role: 'assistant', content: 'Hiện tại tôi chưa trả lời được. Bạn hãy thử lại sau hoặc đặt câu hỏi ngắn gọn hơn.' });
        setText('chatStatus', err.message);
        persistGuestChat();
        renderChat();
    }
}

function beginPatientEdit(patientId) {
    const patient = state.patients.find((item) => item.id === patientId);
    if (!patient) return;
    state.editingPatientId = patientId;
    if (el('patientFullName')) el('patientFullName').value = patient.full_name || '';
    if (el('patientDob')) el('patientDob').value = patient.date_of_birth || '';
    if (el('patientGender')) el('patientGender').value = patient.gender || '';
    if (el('patientNotes')) el('patientNotes').value = patient.notes || '';
    setText('patientFormTitle', 'Chỉnh sửa hồ sơ bệnh nhân');
    setText('patientFormActionText', 'Lưu thay đổi');
    el('cancelPatientEditBtn')?.classList.remove('hidden');
    setStatus('patientStatus', `Đang chỉnh sửa hồ sơ: ${patient.full_name}`, 'muted');
}

function resetPatientForm() {
    state.editingPatientId = null;
    if (el('patientFullName')) el('patientFullName').value = '';
    if (el('patientDob')) el('patientDob').value = '';
    if (el('patientGender')) el('patientGender').value = '';
    if (el('patientNotes')) el('patientNotes').value = '';
    setText('patientFormTitle', 'Tạo hồ sơ bệnh nhân');
    setText('patientFormActionText', 'Tạo bệnh nhân');
    el('cancelPatientEditBtn')?.classList.add('hidden');
}

function ensureDoctorPatientSelected() {
    if (state.currentUser?.role !== 'doctor') return null;
    const patientId = selectedPredictionPatientId() || selectedPatientId();
    if (!patientId) {
        throw new Error('Bác sĩ cần chọn bệnh nhân trước khi thực hiện dự đoán để lưu đúng lịch sử theo hồ sơ.');
    }
    return patientId;
}

// ── Toast notification ─────────────────────────────────────────
let toastTimer = null;
function showToast(message, type = 'normal') {
    const toast = el('statusToast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `status-toast ${type}`;
    toast.classList.remove('hidden');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.classList.add('hidden'); }, 4200);
}

// ── setStatus: backward-compat + toast ────────────────────────
function setStatus(id, message, tone = 'normal') {
    const toastTone = tone === 'error' ? 'error' : tone === 'success' ? 'success' : 'normal';
    showToast(message, toastTone);

    if (id === 'authStatus') {
        document.querySelectorAll('[data-auth-status]').forEach(e => {
            e.textContent = message;
            e.className = 'inline-note';
            if (tone === 'error')   e.classList.add('text-danger');
            if (tone === 'success') e.classList.add('text-success');
            if (tone === 'muted')   e.classList.add('text-muted');
        });
        return;
    }

    const e = el(id);
    if (!e) return;
    e.textContent = message;
    e.className = e.className.replace(/\btext-(danger|success|muted)\b/g, '').trim();
    if (tone === 'error')   e.classList.add('text-danger');
    if (tone === 'success') e.classList.add('text-success');
    if (tone === 'muted')   e.classList.add('text-muted');
}

// ── API fetch wrapper ──────────────────────────────────────────
async function apiFetch(url, options = {}) {
    const headers = new Headers(options.headers || {});
    if (state.authToken) headers.set('Authorization', `Bearer ${state.authToken}`);
    return fetch(url, { ...options, headers });
}

// ================================================================
// NAVIGATION
// ================================================================

const VALID_PAGES = ['home','learn','care','videos','assistant','prediction','stats','about',
                     'history','patients','login','register','recovery','account'];

function navigate(page) {
    if (!VALID_PAGES.includes(page)) page = 'home';
    // Guard: non-doctors cannot access patients page
    if (page === 'patients' && state.currentUser?.role !== 'doctor') {
        page = 'prediction';
    }
    state.currentPage = page;

    document.querySelectorAll('.page').forEach(el => {
        el.classList.toggle('is-active', el.id === `page-${page}`);
    });

    // Desktop nav active state
    document.querySelectorAll('.topbar-nav-link, .mobile-nav-link').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.page === page);
    });

    window.location.hash = page;
    // Close mobile nav if open
    closeMobileNav();
}

function switchPredictTab(tab) {
    const tabChanged = state.currentPredictTab !== tab;
    state.currentPredictTab = tab;
    document.querySelectorAll('.subnav-link').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.predictTab === tab);
    });
    document.querySelectorAll('.predict-panel').forEach(panel => {
        panel.classList.toggle('is-active', panel.id === `predict-tab-${tab}`);
    });
    if (tabChanged) {
        clearPredictionResult();
    }
    if (tab === 'fusion') updateMultimodalPanel();
}

// ── Mobile nav ─────────────────────────────────────────────────
function openMobileNav() {
    const drawer = el('mobileNavDrawer');
    if (drawer) drawer.classList.add('is-open');
}
function closeMobileNav() {
    const drawer = el('mobileNavDrawer');
    if (drawer) drawer.classList.remove('is-open');
}

// ================================================================
// RENDER — static collections
// ================================================================

function renderStaticCollections() {
    // Home highlights
    const homeHighlights = el('homeHighlights');
    if (homeHighlights) homeHighlights.innerHTML = HOME_HIGHLIGHTS.map(item => `
        <article class="highlight-card">
            <p class="eyebrow">${item.tag}</p>
            <h3 style="font-size:1.05rem;">${item.title}</h3>
            <p style="font-size:0.88rem;color:var(--text-700);line-height:1.65;">${item.text}</p>
        </article>`).join('');

    // Learn grid
    const learnGrid = el('learnGrid');
    if (learnGrid) learnGrid.innerHTML = LEARN_ITEMS.map(item => `
        <article class="learn-card">
            <strong>${item.title}</strong>
            <p>${item.text}</p>
        </article>`).join('');

    const learnDeepGrid = el('learnDeepGrid');
    if (learnDeepGrid) learnDeepGrid.innerHTML = LEARN_DEEP.map(item => `
        <article class="card">
            <h3 style="margin-bottom:8px;">${item.title}</h3>
            <p class="section-copy" style="font-size:0.88rem;">${item.text}</p>
        </article>`).join('');

    // FAQ
    const faqList = el('faqList');
    if (faqList) faqList.innerHTML = FAQ_ITEMS.map((item, i) => `
        <div class="faq-item" data-faq="${i}">
            <strong>${item.q}</strong>
            <p>${item.a}</p>
        </div>`).join('');

    // Videos
    const videoGrid = el('videoGrid');
    if (videoGrid) videoGrid.innerHTML = VIDEO_ITEMS.map(item => `
        <article class="embed-card">
            <iframe class="video-embed" src="${item.embed}" title="${item.title}" loading="lazy" allowfullscreen></iframe>
            <span class="video-meta">${item.tag}</span>
            <strong>${item.title}</strong>
            <p>${item.text}</p>
            <a class="link-button" href="${item.link}" target="_blank" rel="noreferrer">Mở trên YouTube</a>
        </article>`).join('');

    // Care lists
    ['careBeforeList','careAfterList','careAvoidList'].forEach(id => {
        const container = el(id);
        if (!container) return;
        const data = id === 'careBeforeList' ? CARE_BEFORE : id === 'careAfterList' ? CARE_AFTER : CARE_AVOID;
        container.innerHTML = data.map(item => `<div class="check-item">${item}</div>`).join('');
    });

    const careFoodGrid = el('careFoodGrid');
    if (careFoodGrid) careFoodGrid.innerHTML = CARE_FOODS.map(item => `
        <div class="mini-card"><strong>${item.title}</strong><p>${item.text}</p></div>`).join('');

    const careSupportGrid = el('careSupportGrid');
    if (careSupportGrid) careSupportGrid.innerHTML = PRODUCT_ITEMS.map(item => `
        <div class="mini-card"><strong>${item.title}</strong><p>${item.text}</p></div>`).join('');

    const careImageGrid = el('careImageGrid');
    if (careImageGrid) careImageGrid.innerHTML = CARE_IMAGES.map(item => `
        <article class="embed-card">
            <img class="care-image" src="${item.src}" alt="${item.title}">
            <strong>${item.title}</strong>
            <p>${item.text}</p>
        </article>`).join('');

    const careSources = el('careSources');
    if (careSources) careSources.innerHTML = CARE_SOURCES.map(item => `
        <div class="source-card">
            <strong>${item.label}</strong>
            <a class="link-button" href="${item.url}" target="_blank" rel="noreferrer">Mở bài viết nguồn ↗</a>
        </div>`).join('');

    const productWarnings = el('productWarnings');
    if (productWarnings) productWarnings.innerHTML = PRODUCT_WARNINGS.map(item => `
        <div class="check-item">${item}</div>`).join('');

    const accountChecklist = el('accountChecklist');
    if (accountChecklist) accountChecklist.innerHTML = ACCOUNT_CHECKLIST.map(item => `
        <div class="check-item">${item}</div>`).join('');

    const chatSuggestionList = el('chatSuggestionList');
    if (chatSuggestionList) chatSuggestionList.innerHTML = CHAT_SUGGESTIONS.map(item => `
        <button class="suggestion-chip" type="button" data-chat-suggestion="${item}">${item}</button>
    `).join('');

    // Stats disclaimers
    const statsDisclaimers = el('statsDisclaimers');
    if (statsDisclaimers) statsDisclaimers.innerHTML = STATS_DISCLAIMERS.map(item => `
        <div class="check-item">${item}</div>`).join('');

    // About lists
    const aboutMlList = el('aboutMlList');
    if (aboutMlList) aboutMlList.innerHTML = ABOUT_ML_LIST.map(item => `
        <div class="check-item">${item}</div>`).join('');

    const aboutDlList = el('aboutDlList');
    if (aboutDlList) aboutDlList.innerHTML = ABOUT_DL_LIST.map(item => `
        <div class="check-item">${item}</div>`).join('');
}

// ── FAQ toggle ─────────────────────────────────────────────────
function bindFaqToggle() {
    document.querySelectorAll('.faq-item').forEach(item => {
        item.addEventListener('click', () => item.classList.toggle('open'));
    });
}

// ── Feature form ───────────────────────────────────────────────
function renderFeatureForm() {
    const container = el('featuresForm');
    if (!container) return;
    container.innerHTML = FEATURES.map(feature => `
        <label class="field">
            <span>${formatFeatureLabel(feature)}</span>
            <input class="input" type="number" step="any" id="feature-${feature}" placeholder="0.0">
        </label>`).join('');
}

// ================================================================
// RENDER — Models & Stats
// ================================================================

function renderModels() {
    const mlOptions = state.mlModels.length
        ? state.mlModels.map(n => `<option value="${n}">${n}</option>`).join('')
        : '<option value="">Không có model ML</option>';
    const dlOptions = state.dlModels.length
        ? state.dlModels.map(n => `<option value="${n}">${n}</option>`).join('')
        : '<option value="">Không có model DL</option>';

    const sMl = el('modelSelect'); if (sMl) sMl.innerHTML = mlOptions;
    const sDl = el('dlModelSelect'); if (sDl) sDl.innerHTML = dlOptions;
    const sFusionMl = el('fusionMlModelSelect'); if (sFusionMl) sFusionMl.innerHTML = mlOptions;
    const sFusionDl = el('fusionDlModelSelect'); if (sFusionDl) sFusionDl.innerHTML = dlOptions;
    updateMultimodalPanel();
}

function renderStatsPage() {
    const mlCount = state.mlModels.length;
    const dlCount = state.dlModels.length;

    setText('statMlCount', mlCount || '—');
    setText('statDlCount', dlCount || '—');
    setText('statPredCount', state.predictionCount || '—');
    setText('homeStatsText', mlCount ? `${mlCount} ML + ${dlCount} DL model` : 'Đang tải thống kê...');

    let bestAcc = 0;
    const benchKeys = Object.keys(state.benchmarks || {});
    benchKeys.forEach(k => {
        const acc = state.benchmarks[k]?.accuracy || 0;
        if (acc > bestAcc) bestAcc = acc;
    });
    setText('statBestAcc', bestAcc ? `${(bestAcc * 100).toFixed(1)}%` : '—');

    const benchTable = el('benchmarksTable');
    if (benchTable) {
        if (!benchKeys.length) {
            benchTable.innerHTML = '<div class="result-empty">Không có dữ liệu benchmark.</div>';
        } else {
            benchTable.innerHTML = `
                <div style="overflow-x:auto;">
                    <table style="width:100%; border-collapse:collapse; font-size:0.88rem;">
                        <thead>
                            <tr style="background:var(--mint-100); text-align:left;">
                                <th style="padding:10px 14px; border-radius:8px 0 0 8px;">Model</th>
                                <th style="padding:10px 14px;">Accuracy</th>
                                <th style="padding:10px 14px;">Sensitivity</th>
                                <th style="padding:10px 14px;">Specificity</th>
                                <th style="padding:10px 14px; border-radius:0 8px 8px 0;">ROC-AUC</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${benchKeys.map(k => {
                                const b = state.benchmarks[k] || {};
                                return `<tr style="border-bottom:1px solid var(--line);">
                                    <td style="padding:10px 14px; font-weight:700;">${k}</td>
                                    <td style="padding:10px 14px;">${b.accuracy != null ? `${(b.accuracy*100).toFixed(1)}%` : '—'}</td>
                                    <td style="padding:10px 14px;">${b.sensitivity != null ? `${(b.sensitivity*100).toFixed(1)}%` : '—'}</td>
                                    <td style="padding:10px 14px;">${b.specificity != null ? `${(b.specificity*100).toFixed(1)}%` : '—'}</td>
                                    <td style="padding:10px 14px;">${b.roc_auc != null ? `${(b.roc_auc*100).toFixed(1)}%` : '—'}</td>
                                </tr>`;
                            }).join('')}
                        </tbody>
                    </table>
                </div>`;
        }
    }

    const dlCards = el('dlModelCards');
    if (dlCards) {
        if (!state.dlModels.length) {
            dlCards.innerHTML = '<div class="result-empty">Không có model DL.</div>';
        } else {
            dlCards.innerHTML = state.dlModels.map(name => `
                <div class="stat-card">
                    <div class="stat-card-value" style="font-size:1.1rem;">${name}</div>
                    <div class="stat-card-label">${name === 'Custom CNN' ? 'Model DL đang dùng trong hệ thống' : 'Model DL đã nạp'}</div>
                </div>`).join('');
        }
    }

    const dlBenchmarkTable = el('dlBenchmarkTable');
    if (dlBenchmarkTable) {
        dlBenchmarkTable.innerHTML = `
            <div style="overflow-x:auto;">
                <table style="width:100%; border-collapse:collapse; font-size:0.88rem;">
                    <thead>
                        <tr style="background:var(--mint-100); text-align:left;">
                            <th style="padding:10px 14px; border-radius:8px 0 0 8px;">Model</th>
                            <th style="padding:10px 14px;">Biến thể</th>
                            <th style="padding:10px 14px;">Accuracy</th>
                            <th style="padding:10px 14px;">Sensitivity</th>
                            <th style="padding:10px 14px;">Specificity</th>
                            <th style="padding:10px 14px; border-radius:0 8px 8px 0;">ROC-AUC</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${DL_RESEARCH_BENCHMARKS.map((item) => `
                            <tr style="border-bottom:1px solid var(--line);">
                                <td style="padding:10px 14px; font-weight:700;">${item.name}</td>
                                <td style="padding:10px 14px;">${item.variant}</td>
                                <td style="padding:10px 14px;">${(item.accuracy * 100).toFixed(1)}%</td>
                                <td style="padding:10px 14px;">${(item.sensitivity * 100).toFixed(1)}%</td>
                                <td style="padding:10px 14px;">${(item.specificity * 100).toFixed(1)}%</td>
                                <td style="padding:10px 14px;">${(item.roc_auc * 100).toFixed(1)}%</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    const dlSelectionSummary = el('dlSelectionSummary');
    if (dlSelectionSummary) {
        dlSelectionSummary.innerHTML = DL_RESEARCH_BENCHMARKS.map((item) => `
            <div class="check-item">
                <strong>${item.name}${item.variant ? ` (${item.variant})` : ''}</strong>: ${item.decision}
            </div>
        `).join('');
    }
}

// ================================================================
// RENDER — Patients & History
// ================================================================

function renderPatients() {
    const select = el('patientSelect');
    const predictionSelect = el('predictionPatientSelect');
    const histSelect = el('historyPatientSelect');
    const currentValue = select ? select.value : '';
    const currentPredictionValue = predictionSelect ? predictionSelect.value : '';
    const isDoctor = state.currentUser?.role === 'doctor';

    const guestOption = isDoctor ? '<option value="">— Chọn bệnh nhân —</option>' : '<option value="">Chế độ khách</option>';
    const patientOpts = state.patients.map(p => `<option value="${p.id}">${p.full_name}</option>`).join('');

    if (select) {
        select.innerHTML = guestOption + patientOpts;
        if (state.patients.some(p => String(p.id) === currentValue)) select.value = currentValue;
        else if (state.patients.length) select.value = String(state.patients[0].id);
    }
    if (predictionSelect) {
        predictionSelect.innerHTML = '<option value="">— Chọn bệnh nhân —</option>' + patientOpts;
        if (state.patients.some(p => String(p.id) === currentPredictionValue)) predictionSelect.value = currentPredictionValue;
        else if (select?.value) predictionSelect.value = select.value;
    }
    if (histSelect) {
        histSelect.innerHTML = isDoctor
            ? '<option value="">— Chọn bệnh nhân để xem lịch sử —</option>' + patientOpts
            : '<option value="">— Lịch sử của tôi —</option>' + patientOpts;
    }

    const filterCard = el('historyPatientFilter');
    if (filterCard) filterCard.classList.toggle('hidden', !isDoctor);
    const predictionCard = el('predictionPatientCard');
    if (predictionCard) predictionCard.classList.toggle('hidden', !isDoctor);
    setText('patientMode', isDoctor ? 'Bác sĩ' : (state.currentUser ? 'Người dùng' : 'Khách'));
    setText('historyStatus', state.currentUser ? 'Đã tải' : 'Chưa đăng nhập');
    setText('predictionPatientHint', isDoctor
        ? (selectedPredictionPatientId() ? 'Kết quả dự đoán sẽ được lưu vào hồ sơ bệnh nhân đang chọn.' : 'Hãy chọn đúng bệnh nhân trước khi chạy dự đoán để lưu kết quả vào đúng hồ sơ.')
        : '');

    const cards = el('patientCards');
    if (!cards) return;
    if (!state.currentUser) {
        cards.innerHTML = '<div class="result-empty">Đăng nhập để xem.</div>';
        return;
    }
    if (!isDoctor) {
        cards.innerHTML = '<div class="result-empty">Chỉ dành cho bác sĩ.</div>';
        return;
    }
    if (!state.patients.length) {
        cards.innerHTML = '<div class="result-empty">Chưa có bệnh nhân.</div>';
        return;
    }
    cards.innerHTML = state.patients.map(p => `
        <div class="patient-card">
            <div class="patient-card-header">
                <strong>${p.full_name}</strong>
                <div class="inline-actions">
                    <button class="btn btn-secondary btn-xs" onclick="showHistoryForPatient(${p.id})">Lịch sử</button>
                    <button class="btn btn-secondary btn-xs" onclick="beginPatientEdit(${p.id})">Sửa</button>
                    <button class="btn btn-danger btn-xs" onclick="deletePatient(${p.id})">Xóa</button>
                </div>
            </div>
            <p>Ngày sinh: ${p.date_of_birth || '—'}</p>
            <p>Giới tính: ${p.gender || '—'}</p>
            <p>Ghi chú: ${p.notes || '—'}</p>
            <small>Cập nhật: ${p.updated_at || ''}</small>
        </div>`).join('');
}

async function showHistoryForPatient(patientId) {
    const s = el('patientSelect');
    const ps = el('predictionPatientSelect');
    const hs = el('historyPatientSelect');
    if (s) s.value = String(patientId);
    if (ps) ps.value = String(patientId);
    if (hs) hs.value = String(patientId);
    await loadPredictionHistory();
    navigate('history');
}

async function deletePatient(patientId) {
    const patient = state.patients.find((item) => item.id === patientId);
    if (!patient) return;
    if (!window.confirm(`Xóa hồ sơ bệnh nhân "${patient.full_name}"?`)) return;
    try {
        const res = await apiFetch(`${API_BASE_URL}/patients/${patientId}/`, { method: 'DELETE' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Xóa bệnh nhân thất bại');
        if (selectedPatientId() === patientId && el('patientSelect')) el('patientSelect').value = '';
        if (selectedPredictionPatientId() === patientId && el('predictionPatientSelect')) el('predictionPatientSelect').value = '';
        if (selectedHistoryPatientId() === patientId && el('historyPatientSelect')) el('historyPatientSelect').value = '';
        resetPatientForm();
        await loadPatients();
        await loadPredictionHistory();
        showToast('Đã xóa bệnh nhân.', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function buildHistoryCardHTML(item) {
    const typeBadgeClass = item.prediction_type === 'ml' ? 'type-ml' : item.prediction_type === 'dl' ? 'type-dl' : 'type-fusion';
    const typeLabel = (item.prediction_type || '').toUpperCase();
    const diagClass = badgeClass(item.diagnosis, item.risk_band);
    const responsePayload = item.response_payload || {};
    const explSrc = resolveExplanationImage(responsePayload.explanation_image || item.explanation_image);
    const fusionMl = responsePayload.ml_result || null;
    const fusionDl = responsePayload.dl_result || null;
    const fusionDlHeatmap = resolveExplanationImage(fusionDl?.explanation_image);
    const advice = cleanNarrative(item.advice || responsePayload.advice || '');
    const adviceSource = renderAdviceSource(item.advice_provider || responsePayload.advice_provider, item.advice_model || responsePayload.advice_model);
    const adviceHtml = advice ? advice.replace(/\n/g, '<br>') : 'Chưa có lời khuyên AI cho lần dự đoán này.';
    const historySecondaryBlock = item.prediction_type === 'ml'
        ? `<div class="detail-analysis" style="background:#fff;"><strong>Lời khuyên từ AI:</strong><br>${adviceHtml}</div>`
        : item.prediction_type === 'dl'
            ? (explSrc ? `<div class="detail-heatmap-wrap compact">
                <div><div class="detail-block-label">Ảnh giải thích</div><img src="${explSrc}" alt="Explanation"></div>
            </div>` : '<div class="result-empty">Không có ảnh giải thích cho lần dự đoán này.</div>')
            : (fusionDlHeatmap
                ? `<div class="detail-heatmap-wrap compact">
                    <div><div class="detail-block-label">Heatmap nhánh DL</div><img src="${fusionDlHeatmap}" alt="Fusion DL explanation"></div>
                </div>`
                : `<div class="detail-analysis" style="background:#fff;"><strong>Lời khuyên từ AI:</strong><br>${adviceHtml}</div>`);
    const historyPrimaryBlock = item.prediction_type === 'ml'
        ? `<div class="detail-analysis"><strong>SHAP / Yếu tố chính:</strong>${renderHistoryTopFeatures(responsePayload)}</div>`
        : item.prediction_type === 'dl'
            ? `<div class="detail-analysis" style="background:#fff;"><strong>Lời khuyên từ AI:</strong><br>${adviceHtml}</div>`
            : `<div class="detail-analysis" style="background:#fff;">
                <strong>Tín hiệu hợp nhất:</strong><br>
                Nhánh ML: ${translateDiagnosis(fusionMl?.diagnosis)} (${formatPercent(fusionMl?.probability)})<br>
                Nhánh DL: ${translateDiagnosis(fusionDl?.diagnosis)} (${formatPercent(fusionDl?.probability)})<br>
                Kết luận kết hợp: ${translateDiagnosis(responsePayload.combined_diagnosis || item.diagnosis)} (${formatPercent(responsePayload.combined_confidence || item.probability)})
            </div>`;

    const detailContent = `
        <div class="history-detail-panel">
            <div class="detail-grid">
                <div class="detail-block">
                    <div class="detail-block-label">Chẩn đoán</div>
                    <div class="detail-block-value"><span class="result-badge ${diagClass}">${translateDiagnosis(item.diagnosis)}</span></div>
                </div>
                <div class="detail-block">
                    <div class="detail-block-label">Xác suất</div>
                    <div class="detail-block-value">${formatPercent(item.probability)}</div>
                </div>
                <div class="detail-block">
                    <div class="detail-block-label">Mức nguy cơ</div>
                    <div class="detail-block-value">${translateRiskBand(item.risk_band)}</div>
                </div>
                <div class="detail-block">
                    <div class="detail-block-label">Mô hình</div>
                    <div class="detail-block-value">${item.model_name || '—'}</div>
                </div>
                <div class="detail-block">
                    <div class="detail-block-label">Thời gian</div>
                    <div class="detail-block-value" style="font-size:0.75rem;">${item.created_at || '—'}</div>
                </div>
            </div>
            ${item.analysis_text ? `<div class="detail-analysis"><strong>Phân tích:</strong><br>${cleanNarrative(item.analysis_text).replace(/\n/g, '<br>')}</div>` : ''}
            ${adviceSource}
            <div class="result-detail-grid">
                ${historyPrimaryBlock}
                ${historySecondaryBlock}
            </div>
        </div>`;

    return `
    <div class="history-card" onclick="this.classList.toggle('is-open')">
        <div class="history-card-header">
            <div class="history-card-meta">
                <div class="history-card-title"><span class="history-type-badge ${typeBadgeClass}">${typeLabel}</span> ${translateDiagnosis(item.diagnosis)}</div>
                <div class="history-card-sub">${item.model_name || '—'} · ${item.created_at || ''}</div>
            </div>
            <div class="history-card-actions">
                <span class="result-badge ${diagClass}">${formatPercent(item.probability)}</span>
                <div class="history-open-text">Xem chi tiết</div>
                <div class="chevron-icon">▾</div>
            </div>
        </div>
        ${detailContent}
    </div>`;
}

function renderHistory() {
    const userHistEl = el('userHistoryList');
    const patientHistEl = el('historyList');
    const isDoctor = state.currentUser?.role === 'doctor';
    const hasHistoryPatient = !!selectedHistoryPatientId();
    const historyItems = isDoctor && hasHistoryPatient ? state.doctorPatientHistory : state.history;

    if (userHistEl) {
        if (!state.currentUser) {
            userHistEl.innerHTML = '<div class="result-empty">Đăng nhập để xem.</div>';
        } else if (isDoctor && !hasHistoryPatient) {
            userHistEl.innerHTML = '<div class="result-empty">Chọn một bệnh nhân để xem lịch sử dự đoán theo từng hồ sơ.</div>';
        } else if (!historyItems.length) {
            userHistEl.innerHTML = '<div class="result-empty">Chưa có lịch sử.</div>';
        } else {
            userHistEl.innerHTML = historyItems.map(item => buildHistoryCardHTML(item)).join('');
        }
    }
    if (patientHistEl) {
        if (!state.currentUser) patientHistEl.innerHTML = '<div class="result-empty">Đăng nhập để xem.</div>';
        else if (!state.patientHistory.length) patientHistEl.innerHTML = '<div class="result-empty">Chưa có lịch sử.</div>';
        else patientHistEl.innerHTML = state.patientHistory.map(item => buildHistoryCardHTML(item)).join('');
    }

    const title = el('historyPageTitle');
    const historyPatient = state.patients.find(p => p.id === selectedHistoryPatientId());
    if (title) {
        if (isDoctor && historyPatient) title.textContent = `Lịch sử dự đoán: ${historyPatient.full_name}`;
        else if (isDoctor) title.textContent = 'Lịch sử dự đoán theo bệnh nhân';
        else title.textContent = 'Lịch sử dự đoán cá nhân';
    }
    
    setText('workspaceHistoryCount', String(state.currentUser?.role === 'doctor' ? state.patientHistory.length : state.history.length));
}

// ================================================================
// AUTH & DATA SYNC
// ================================================================

async function syncCurrentUser() {
    const previousUserId = state.currentUser?.id ?? null;
    if (!state.authToken) {
        state.currentUser = null;
        state.history = [];
        state.patientHistory = [];
        state.doctorPatientHistory = [];
        state.patients = [];
        state.chatTurns = [];
        localStorage.removeItem('bcai_token');
        localStorage.removeItem('bcai_user');
        resetPredictionWorkspace();
        return;
    }
    try {
        const res = await apiFetch(`${API_BASE_URL}/auth/me/`);
        if (!res.ok) throw new Error('Phiên đã hết hạn');
        state.currentUser = await res.json();
        localStorage.setItem('bcai_user', JSON.stringify(state.currentUser));
        if (previousUserId !== null && previousUserId !== state.currentUser?.id) {
            resetPredictionWorkspace();
        }
    } catch {
        state.authToken = '';
        state.currentUser = null;
        state.history = [];
        state.patientHistory = [];
        state.doctorPatientHistory = [];
        state.patients = [];
        state.chatTurns = [];
        localStorage.removeItem('bcai_token');
        localStorage.removeItem('bcai_user');
        resetPredictionWorkspace();
    }
}

async function loadModels() {
    try {
        const [mlRes, benchRes, dlRes] = await Promise.all([
            fetch(`${API_BASE_URL}/models/`),
            fetch(`${API_BASE_URL}/models/benchmarks/`),
            fetch(`${API_BASE_URL}/models/dl/`),
        ]);
        state.mlModels = mlRes.ok ? await mlRes.json() : [];
        state.benchmarks = benchRes.ok ? await benchRes.json() : {};
        state.dlModels = dlRes.ok ? await dlRes.json() : [];
        
        renderModels();
        renderStatsPage();
    } catch {
        state.mlModels = []; state.dlModels = []; state.benchmarks = {};
    }
}

async function loadPatients() {
    if (!state.authToken) { state.patients = []; renderPatients(); return; }
    try {
        const res = await apiFetch(`${API_BASE_URL}/patients/`);
        if (res.status === 403) { state.patients = []; }
        else if (res.ok) { state.patients = await res.json(); }
    } catch { state.patients = []; }
    renderPatients();
}

async function loadPredictionHistory() {
    if (!state.authToken) {
        state.history = [];
        state.patientHistory = [];
        state.doctorPatientHistory = [];
        renderHistory();
        return;
    }
    try {
        if (state.currentUser?.role === 'doctor') {
            const patientId = selectedPatientId();
            const historyPatientId = selectedHistoryPatientId();
            const [ownRes, patientRes] = await Promise.all([
                apiFetch(`${API_BASE_URL}/predictions/history/`),
                patientId
                    ? apiFetch(`${API_BASE_URL}/predictions/history/?patient_id=${patientId}`)
                    : Promise.resolve(null),
            ]);
            const historyFilterRes = historyPatientId
                ? await apiFetch(`${API_BASE_URL}/predictions/history/?patient_id=${historyPatientId}`)
                : null;
            
            state.history = ownRes?.ok ? await ownRes.json() : [];
            state.patientHistory = patientRes?.ok ? await patientRes.json() : [];
            state.doctorPatientHistory = historyFilterRes?.ok ? await historyFilterRes.json() : [];
        } else {
            const res = await apiFetch(`${API_BASE_URL}/predictions/history/`);
            state.history = res.ok ? await res.json() : [];
            state.patientHistory = state.history;
            state.doctorPatientHistory = [];
        }
    } catch {
        state.history = [];
        state.patientHistory = [];
        state.doctorPatientHistory = [];
    }
    renderHistory();
}

async function refreshAll() {
    await syncCurrentUser();
    await Promise.all([loadModels(), loadPatients(), loadPredictionHistory(), loadChatHistory()]);
    updateAccountUI();
}

function updateAccountUI() {
    const user = state.currentUser;
    setText('sessionBadge', user ? user.full_name : 'Khách');
    setText('accountName', user ? user.full_name : 'Khách');
    setText('accountEmail', user ? user.email : 'Chưa đăng nhập');
    setText('accountRole', user ? (user.role === 'doctor' ? 'Bác sĩ' : 'Người dùng') : '—');
    setText('accountPatientCount', String(state.patients.length));

    const avatarInitials = el('avatarInitials');
    if (avatarInitials) avatarInitials.textContent = initialsFromName(user?.full_name || 'Khách');

    const guestActions = el('guestActions');
    const userMenu = el('userMenu');
    if (guestActions) guestActions.classList.toggle('hidden', !!user);
    if (userMenu) userMenu.classList.toggle('hidden', !user);

    const isDoctor = user?.role === 'doctor';
    ['patientsNavBtn', 'doctorMenuLink', 'mobilePatientsLink', 'page-patients'].forEach(id => {
        const e = el(id); if (e) e.classList.toggle('hidden', !isDoctor);
    });
    ['historyNavBtn', 'mobileHistoryLink'].forEach(id => {
        const e = el(id); if (e) e.classList.toggle('hidden', !user);
    });

    setStatus('authStatus', user ? `Đang đăng nhập: ${user.full_name}` : 'Chưa đăng nhập', user ? 'success' : 'muted');
}

async function loginUser() {
    const payload = { email: el('loginEmail').value.trim(), password: el('loginPassword').value };
    try {
        const res = await fetch(`${API_BASE_URL}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Login failed');
        state.authToken = data.access_token;
        state.currentUser = data.user;
        localStorage.setItem('bcai_token', data.access_token);
        localStorage.setItem('bcai_user', JSON.stringify(data.user));
        resetPredictionWorkspace();
        await refreshAll();
        navigate('prediction');
    } catch (err) { setStatus('authStatus', err.message, 'error'); }
}

async function registerUser() {
    const payload = {
        full_name: el('registerFullName').value.trim(),
        email: el('registerEmail').value.trim(),
        role: el('registerRole').value,
        password: el('registerPassword').value
    };
    try {
        const res = await fetch(`${API_BASE_URL}/auth/register/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Registration failed');
        state.authToken = data.access_token;
        state.currentUser = data.user;
        localStorage.setItem('bcai_token', data.access_token);
        localStorage.setItem('bcai_user', JSON.stringify(data.user));
        resetPredictionWorkspace();
        await refreshAll();
        navigate(data.user.role === 'doctor' ? 'patients' : 'prediction');
    } catch (err) { setStatus('authStatus', err.message, 'error'); }
}

async function logoutUser() {
    try { if (state.authToken) await apiFetch(`${API_BASE_URL}/auth/logout/`, { method: 'POST' }); }
    finally {
        state.authToken = ''; state.currentUser = null; state.patients = []; state.history = []; state.patientHistory = []; state.doctorPatientHistory = []; state.chatTurns = [];
        localStorage.removeItem('bcai_token'); localStorage.removeItem('bcai_user');
        resetPredictionWorkspace();
        await refreshAll();
        navigate('home');
    }
}

// ================================================================
// PREDICTION LOGIC
// ================================================================

function collectClinicalPayload() {
    const payload = {};
    for (const f of FEATURES) {
        const input = el(`feature-${f}`);
        if (!input.value.trim()) throw new Error(`Thiếu giá trị cho ${formatFeatureLabel(f)}`);
        const val = Number(input.value);
        if (Number.isNaN(val)) throw new Error(`Giá trị không hợp lệ cho ${formatFeatureLabel(f)}`);
        payload[f] = val;
    }
    return payload;
}

function parseClinicalCsvText(csvText) {
    const lines = String(csvText || '').trim().split(/\r?\n/);
    if (lines.length < 2) throw new Error('CSV không hợp lệ, cần có ít nhất 2 dòng (header + dữ liệu).');
    const headers = lines[0].split(',').map((s) => s.trim());
    const values = lines[1].split(',').map((s) => s.trim());
    const payload = {};
    FEATURES.forEach((feature) => {
        const index = headers.indexOf(feature);
        if (index < 0) return;
        const raw = values[index];
        const numeric = Number(raw);
        if (!Number.isNaN(numeric)) payload[feature] = numeric;
    });
    return payload;
}

function validateClinicalPayload(payload) {
    const missing = FEATURES.filter((feature) => {
        const value = payload?.[feature];
        return value === null || value === undefined || Number.isNaN(Number(value));
    });
    return { ok: missing.length === 0, missing };
}

function loadSampleData(type) {
    const sample = SAMPLES[type];
    FEATURES.forEach(f => {
        const input = el(`feature-${f}`);
        if (input) input.value = sample[f];
    });
    el('refreshPatientsBtn')?.addEventListener('click', loadPatients);
    updateMultimodalPanel();
    setStatus('predictionStatus', `Đã nạp dữ liệu mẫu ${type === 'benign' ? 'lành tính' : 'ác tính'}.`, 'success');
}

function fillClinicalValues(values) {
    let filled = 0;
    FEATURES.forEach((feature) => {
        const input = el(`feature-${feature}`);
        if (!input) return;
        const value = values?.[feature];
        if (value === null || value === undefined || Number.isNaN(Number(value))) return;
        input.value = String(value);
        filled += 1;
    });
    updateMultimodalPanel();
    return filled;
}

function setFusionClinicalValues(values) {
    state.fusionClinicalData = {};
    FEATURES.forEach((feature) => {
        const value = values?.[feature];
        if (value === null || value === undefined || Number.isNaN(Number(value))) return;
        state.fusionClinicalData[feature] = Number(value);
    });
    updateMultimodalPanel();
    return countFilledFusionClinicalInputs();
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function renderTopFeatures(features) {
    if (!Array.isArray(features) || !features.length) {
        return '<p class="result-empty">Chưa có giải thích đặc trưng cho lần dự đoán này.</p>';
    }

    return `
        <div class="result-feature-list">
            ${features.slice(0, 6).map((feat) => `
                <div class="result-feature-item">
                    <strong>${escapeHtml(formatFeatureLabel(feat.feature || 'Đặc trưng'))}</strong>
                    <p>${escapeHtml(feat.description || feat.impact_label || feat.direction || 'Tín hiệu được hệ thống chú ý.')}</p>
                </div>
            `).join('')}
        </div>
    `;
}

function renderHistoryTopFeatures(responsePayload) {
    const topFeatures = responsePayload?.top_features;
    if (!Array.isArray(topFeatures) || !topFeatures.length) {
        return '<div class="result-empty">Không có dữ liệu SHAP cho lần dự đoán này.</div>';
    }
    return `
        <div class="history-feature-list">
            ${topFeatures.slice(0, 5).map((feat) => `
                <div class="history-feature-item">
                    <strong>${escapeHtml(formatFeatureLabel(feat.feature || 'Đặc trưng'))}</strong>
                    <p>${escapeHtml(feat.description || feat.impact_label || feat.direction || 'Yếu tố được hệ thống chú ý.')}</p>
                </div>
            `).join('')}
        </div>
    `;
}

function renderAdviceBlock(advice, emptyText = 'Chưa có lời khuyên AI cho lần dự đoán này.') {
    if (!advice) {
        return `<p class="result-empty">${escapeHtml(emptyText)}</p>`;
    }
    return `<div class="detail-analysis" style="background:#fff;">${escapeHtml(advice).replace(/\n/g, '<br>')}</div>`;
}

function renderAdviceSource(provider, model) {
    const source = String(provider || '').trim();
    const modelText = String(model || '').trim();
    if (!source) return '';
    const label = source === 'gemini'
        ? 'Nguồn lời khuyên: Gemini'
        : source === 'openai'
            ? 'Nguồn lời khuyên: OpenAI'
            : source.endsWith('_unavailable')
                ? 'Nguồn lời khuyên: AI hiện không khả dụng'
                : 'Nguồn lời khuyên: local fallback';
    return `<p class="result-note">${escapeHtml(label)}${modelText ? ` (${escapeHtml(modelText)})` : ''}</p>`;
}

function renderFusionBranchCard(title, result, options = {}) {
    const diagnosis = translateDiagnosis(result?.diagnosis);
    const diagClass = result?.diagnosis === 'Malignant' ? 'malignant' : (result?.risk_band === 'Medium' ? 'medium' : 'benign');
    const topFeaturesHtml = options.showFeatures ? renderTopFeatures(result?.top_features) : '';
    const explanationSrc = options.showImage ? resolveExplanationImage(result?.explanation_image) : null;
    const explanationHtml = explanationSrc
        ? `
            <figure class="result-figure">
                <img class="result-heatmap" src="${escapeHtml(explanationSrc)}" alt="Ảnh giải thích từ nhánh DL">
                <figcaption>Heatmap của nhánh DL trong pipeline đa phương thức.</figcaption>
            </figure>
        `
        : '<p class="result-empty">Nhánh này không trả ảnh giải thích riêng.</p>';

    return `
        <article class="result-block">
            <h4>${escapeHtml(title)}</h4>
            <div class="result-primary-meta" style="margin-bottom:10px;">
                <span class="result-badge ${diagClass}">${escapeHtml(diagnosis)}</span>
                <strong class="result-primary-probability">${formatPercent(result?.probability)}</strong>
            </div>
            <ul class="result-list">
                <li>Mô hình: <strong>${escapeHtml(result?.model_name || '—')}</strong></li>
                <li>Nguy cơ: <strong>${escapeHtml(translateRiskBand(result?.risk_band))}</strong></li>
                <li>Xác suất gốc: <strong>${formatPercent(result?.raw_probability)}</strong></li>
            </ul>
            ${options.showFeatures ? `<div style="margin-top:12px;">${topFeaturesHtml}</div>` : ''}
            ${options.showImage ? `<div style="margin-top:12px;">${explanationHtml}</div>` : ''}
        </article>
    `;
}

function renderFusionResultHtml(result) {
    const combinedDiagnosis = result?.combined_diagnosis || 'Benign';
    const combinedRiskBand = result?.combined_risk_band || 'Medium';
    const diagClass = combinedDiagnosis === 'Malignant' ? 'malignant' : (combinedRiskBand === 'Medium' ? 'medium' : 'benign');
    const advice = cleanNarrative(result?.advice || '');
    const adviceSource = renderAdviceSource(result?.advice_provider, result?.advice_model);
    const mlResult = result?.ml_result || {};
    const dlResult = result?.dl_result || {};
    const synthesis = [
        `Nhánh ML (${mlResult.model_name || 'ML'}) đánh giá ${translateDiagnosis(mlResult.diagnosis)} với xác suất ${formatPercent(mlResult.probability)}.`,
        `Nhánh DL (${dlResult.model_name || 'DL'}) đánh giá ${translateDiagnosis(dlResult.diagnosis)} với xác suất ${formatPercent(dlResult.probability)}.`,
        'Hệ thống kết hợp hai tín hiệu với trọng số ưu tiên ảnh nhũ ảnh để tạo ra kết luận cuối cùng.'
    ].join(' ');

    return `
        <div class="result-stack">
            <div class="result-header-block">
                <p class="eyebrow">Kết quả đa phương thức</p>
                <h4>Kết luận tổng hợp từ ML và DL</h4>
                <p class="result-header-copy">Kết quả dưới đây kết hợp dữ liệu lâm sàng và ảnh nhũ ảnh. Đây là lớp suy luận tổng hợp dùng để hỗ trợ sàng lọc tốt hơn so với chỉ dùng một nguồn dữ liệu.</p>
            </div>
            <div class="result-grid">
                <article class="result-block result-primary-block">
                    <h4>Kết luận kết hợp</h4>
                    <div class="result-primary-meta">
                        <span class="result-badge ${diagClass}">${escapeHtml(translateDiagnosis(combinedDiagnosis))}</span>
                        <strong class="result-primary-probability">${formatPercent(result?.combined_confidence)}</strong>
                    </div>
                    <p class="result-note">Độ tin cậy của kết luận tổng hợp.</p>
                </article>
                <article class="result-block">
                    <h4>Tóm tắt nguy cơ</h4>
                    <ul class="result-list">
                        <li>Nguy cơ tổng hợp: <strong>${escapeHtml(translateRiskBand(combinedRiskBand))}</strong></li>
                        <li>Nhánh ML: <strong>${escapeHtml(translateDiagnosis(mlResult.diagnosis))}</strong> (${formatPercent(mlResult.probability)})</li>
                        <li>Nhánh DL: <strong>${escapeHtml(translateDiagnosis(dlResult.diagnosis))}</strong> (${formatPercent(dlResult.probability)})</li>
                    </ul>
                </article>
                <article class="result-block">
                    <h4>Tư vấn</h4>
                    <p>${advice ? escapeHtml(advice).replace(/\n/g, '<br>') : 'Chưa có tư vấn trả về cho lần dự đoán này.'}</p>
                    ${adviceSource}
                </article>
            </div>
            <div class="result-detail-grid">
                ${renderFusionBranchCard('Nhánh ML lâm sàng', mlResult, { showFeatures: true })}
                ${renderFusionBranchCard('Nhánh DL hình ảnh', dlResult, { showImage: true })}
            </div>
            <article class="result-block result-full-width">
                <h4>Nhận định</h4>
                <div class="result-meta-row">
                    <span>Trọng số kết hợp: <strong>ML 40% · DL 60%</strong></span>
                    <span>Chế độ: <strong>Fusion</strong></span>
                </div>
                <p>${escapeHtml(synthesis)}</p>
            </article>
        </div>
    `;
}

function renderResultHtml(result, type = 'ml') {
    if (type === 'fusion') return renderFusionResultHtml(result);
    const diagnosis = translateDiagnosis(result.diagnosis);
    const riskBand = translateRiskBand(result.risk_band);
    const diagClass = result.diagnosis === 'Malignant' ? 'malignant' : (result.risk_band === 'Medium' ? 'medium' : 'benign');
    const analysis = cleanNarrative(result.analysis_text || '');
    const advice = cleanNarrative(result.advice || '');
    const adviceSource = renderAdviceSource(result.advice_provider, result.advice_model);
    const explanationSrc = resolveExplanationImage(result.explanation_image);
    const title = type === 'dl' ? 'Kết quả DL hình ảnh' : type === 'fusion' ? 'Kết quả kết hợp' : 'Kết quả ML lâm sàng';
    const defaultExplanationSection = explanationSrc
        ? `
            <figure class="result-figure">
                <img class="result-heatmap" src="${escapeHtml(explanationSrc)}" alt="Ảnh heatmap vùng hệ thống chú ý">
                <figcaption>Ảnh giải thích cho thấy vùng hệ thống chú ý nhiều hơn trong quá trình phân tích.</figcaption>
            </figure>
        `
        : '<p class="result-empty">Lần chạy này chưa trả ảnh giải thích.</p>';
    let detailGridHtml = `
        <div class="result-detail-grid">
            <article class="result-block">
                <h4>Yếu tố chính</h4>
                ${renderTopFeatures(result.top_features)}
            </article>
            <article class="result-block">
                <h4>Lời khuyên từ AI</h4>
                ${renderAdviceBlock(advice)}
                ${adviceSource}
            </article>
        </div>
    `;

    if (type === 'dl') {
        detailGridHtml = `
            <div class="result-detail-grid">
                <article class="result-block">
                    <h4>Lời khuyên từ AI</h4>
                    ${renderAdviceBlock(advice)}
                    ${adviceSource}
                </article>
                <article class="result-block">
                    <h4>Ảnh giải thích</h4>
                    ${defaultExplanationSection}
                </article>
            </div>
        `;
    } else if (type === 'fusion') {
        detailGridHtml = `
            <div class="result-detail-grid">
                <article class="result-block">
                    <h4>Lời khuyên từ AI</h4>
                    ${renderAdviceBlock(advice)}
                    ${adviceSource}
                </article>
                <article class="result-block">
                    <h4>Tổng hợp tín hiệu</h4>
                    <p class="result-empty">Dự đoán kết hợp không có SHAP hoặc ảnh giải thích riêng. Hãy xem phần nhận định và lời khuyên từ AI.</p>
                </article>
            </div>
        `;
    }

    return `
        <div class="result-stack">
            <div class="result-header-block">
                <p class="eyebrow">Kết quả</p>
                <h4>Kết quả sàng lọc gần nhất</h4>
                <p class="result-header-copy">Dưới đây là bản tóm tắt kết quả dự đoán, mức nguy cơ, lời khuyên và phần giải thích cho lần chạy gần nhất.</p>
            </div>
            <div class="result-grid">
                <article class="result-block result-primary-block">
                    <h4>${escapeHtml(title)}</h4>
                    <div class="result-primary-meta">
                        <span class="result-badge ${diagClass}">${escapeHtml(diagnosis)}</span>
                        <strong class="result-primary-probability">${formatPercent(result.probability)}</strong>
                    </div>
                    <p class="result-note">Xác suất hiển thị cho người dùng.</p>
                </article>
                <article class="result-block">
                    <h4>Tóm tắt nguy cơ</h4>
                    <ul class="result-list">
                        <li>Nguy cơ hiện tại: <strong>${escapeHtml(riskBand)}</strong></li>
                        <li>Xác suất hiển thị: <strong>${formatPercent(result.probability)}</strong></li>
                        <li>Xác suất gốc của mô hình: <strong>${formatPercent(result.raw_probability)}</strong></li>
                    </ul>
                </article>
                <article class="result-block">
                    <h4>Tư vấn</h4>
                    <p>${advice ? escapeHtml(advice).replace(/\n/g, '<br>') : 'Chưa có tư vấn trả về cho lần dự đoán này.'}</p>
                </article>
            </div>

            ${detailGridHtml}

            <article class="result-block result-full-width">
                <h4>Nhận định</h4>
                <div class="result-meta-row">
                    <span>Mô hình: <strong>${escapeHtml(result.model_name || 'Không rõ')}</strong></span>
                    <span>Chế độ hiệu chỉnh: <strong>${escapeHtml(result.calibration_mode || 'N/A')}</strong></span>
                </div>
                <p>${analysis ? escapeHtml(analysis).replace(/\n/g, '<br>') : 'Chưa có nhận định chi tiết cho lần dự đoán này.'}</p>
            </article>
        </div>
    `;
}

function showResult(data, type = 'ml') {
    const resultCard = el('resultCard');
    if (resultCard) resultCard.style.display = 'block';
    const content = el('resultContent');
    if (content) {
        content.classList.remove('result-empty');
        content.innerHTML = renderResultHtml(data, type);
    }
    resultCard?.scrollIntoView({ behavior: 'smooth' });
}

async function predictMl() {
    try {
        const payload = collectClinicalPayload();
        const modelName = el('modelSelect').value;
        const patientId = ensureDoctorPatientSelected() ?? selectedPatientId();
        setStatus('predictionStatus', 'Đang chạy dự đoán ML...', 'muted');
        const url = new URL(`${API_BASE_URL}/predict/`, window.location.origin);
        if (modelName) url.searchParams.set('model_name', modelName);
        if (patientId) url.searchParams.set('patient_id', String(patientId));
        
        const res = await apiFetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Dự đoán ML thất bại');
        
        showResult(data, 'ml');
        setStatus('predictionStatus', 'Hoàn tất dự đoán lâm sàng.', 'success');
        state.predictionCount++;
        await loadPredictionHistory();
    } catch (err) { setStatus('predictionStatus', err.message, 'error'); }
}

async function predictDl() {
    if (!state.selectedDlImageFile) { setStatus('predictionStatus', 'Hãy tải ảnh lên trước.', 'error'); return; }
    try {
        const modelName = el('dlModelSelect').value;
        const patientId = ensureDoctorPatientSelected() ?? selectedPatientId();
        const formData = new FormData();
        formData.append('file', state.selectedDlImageFile);
        
        setStatus('predictionStatus', 'Đang chạy dự đoán ảnh...', 'muted');
        const url = new URL(`${API_BASE_URL}/predict/image/`, window.location.origin);
        if (modelName) url.searchParams.set('model_name', modelName);
        if (patientId) url.searchParams.set('patient_id', String(patientId));
        url.searchParams.set('include_explanation', 'true');
        
        const res = await apiFetch(url, { method: 'POST', body: formData });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Dự đoán DL thất bại');
        
        showResult(data, 'dl');
        setStatus('predictionStatus', 'Hoàn tất dự đoán ảnh.', 'success');
        state.predictionCount++;
        await loadPredictionHistory();
    } catch (err) { setStatus('predictionStatus', err.message, 'error'); }
}

async function predictFusion() {
    if (!state.selectedFusionImageFile) {
        setStatus('predictionStatus', 'Hãy chọn ảnh nhũ ảnh trước khi chạy dự đoán kết hợp.', 'error');
        return;
    }
    try {
        const clinicalPayload = state.fusionClinicalData || {};
        const validation = validateClinicalPayload(clinicalPayload);
        if (!validation.ok) {
            throw new Error(`CSV lâm sàng chưa đủ dữ liệu (${FEATURES.length - validation.missing.length}/${FEATURES.length}).`);
        }
        const mlModel = el('fusionMlModelSelect')?.value || el('modelSelect')?.value || '';
        const dlModel = el('fusionDlModelSelect')?.value || el('dlModelSelect')?.value || '';
        const patientId = ensureDoctorPatientSelected() ?? selectedPatientId();
        const formData = new FormData();
        formData.append('clinical_data', JSON.stringify(clinicalPayload));
        formData.append('image_file', state.selectedFusionImageFile);
        if (mlModel) formData.append('ml_model', mlModel);
        if (dlModel) formData.append('dl_model', dlModel);
        formData.append('include_explanation', 'true');
        if (patientId) formData.append('patient_id', String(patientId));

        setStatus('predictionStatus', 'Đang chạy dự đoán đa phương thức...', 'muted');
        const res = await apiFetch(`${API_BASE_URL}/predict/multimodal/`, {
            method: 'POST',
            body: formData,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Dự đoán đa phương thức thất bại');

        showResult(data, 'fusion');
        setStatus('predictionStatus', 'Hoàn tất dự đoán kết hợp.', 'success');
        state.predictionCount++;
        await loadPredictionHistory();
    } catch (err) {
        setStatus('predictionStatus', err.message, 'error');
    }
}

async function extractClinicalFromImage(file, mode = 'ml') {
    if (!file) return;
    try {
        const formData = new FormData();
        formData.append('file', file);
        setStatus('predictionStatus', 'Đang đọc phiếu xét nghiệm từ ảnh...', 'muted');
        const res = await apiFetch(`${API_BASE_URL}/predict/extract-clinical/`, {
            method: 'POST',
            body: formData,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Không đọc được phiếu xét nghiệm.');
        const filled = mode === 'fusion'
            ? setFusionClinicalValues(data.values || {})
            : fillClinicalValues(data.values || {});
        const providerLabel = String(data.provider || '').startsWith('local_ocr')
            ? 'OCR local'
            : data.provider === 'gemini'
                ? 'Gemini'
                : data.provider === 'openai'
                    ? 'OpenAI'
                    : 'AI';
        setStatus(
            'predictionStatus',
            `Đã điền ${filled}/30 chỉ số từ ảnh bằng ${providerLabel}.`,
            filled > 0 ? 'success' : 'warn',
        );
        showToast(`Hệ thống đã điền ${filled}/30 chỉ số từ ảnh phiếu xét nghiệm.`, filled > 0 ? 'success' : 'error');
        updateMultimodalPanel();
        switchPredictTab(mode === 'fusion' ? 'fusion' : 'ml');
    } catch (err) {
        setStatus('predictionStatus', err.message, 'error');
        showToast(err.message, 'error');
    }
}


// ================================================================
// EVENT BINDINGS & INIT
// ================================================================

function bindEvents() {
    // Navigation
    document.querySelectorAll('[data-page]').forEach(btn => btn.addEventListener('click', () => navigate(btn.dataset.page)));
    document.querySelectorAll('[data-nav-target]').forEach(btn => btn.addEventListener('click', () => navigate(btn.dataset.navTarget)));
    document.querySelectorAll('.subnav-link').forEach(btn => btn.addEventListener('click', () => switchPredictTab(btn.dataset.predictTab)));
    el('brandHomeBtn')?.addEventListener('click', () => navigate('home'));
    
    // Auth
    el('loginBtn')?.addEventListener('click', loginUser);
    el('registerBtn')?.addEventListener('click', registerUser);
    el('logoutBtn')?.addEventListener('click', logoutUser);
    el('menuLogoutBtn')?.addEventListener('click', logoutUser);
    el('logoutAllBtn')?.addEventListener('click', async () => {
        try { if (state.authToken) await apiFetch(`${API_BASE_URL}/auth/logout-all/`, { method: 'POST' }); }
        finally { await logoutUser(); }
    });
    
    // Profile
    el('updateProfileBtn')?.addEventListener('click', async () => {
        const fn = el('profileFullName').value.trim();
        try {
            const res = await apiFetch(`${API_BASE_URL}/auth/profile/`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ full_name: fn })
            });
            if (res.ok) { showToast('Đã cập nhật hồ sơ.', 'success'); await refreshAll(); }
        } catch (err) { showToast(err.message, 'error'); }
    });
    
    // Recovery
    el('forgotPasswordBtn')?.addEventListener('click', async () => {
        const email = el('forgotEmail').value.trim();
        try {
            const res = await fetch(`${API_BASE_URL}/auth/forgot-password/`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await res.json();
            if (res.ok && data.reset_token) el('resetToken').value = data.reset_token;
            showToast(data.message || 'Check outbox.', 'success');
        } catch (err) { showToast(err.message, 'error'); }
    });
    el('resetPasswordBtn')?.addEventListener('click', async () => {
        const payload = { token: el('resetToken').value.trim(), new_password: el('resetNewPassword').value };
        try {
            const res = await fetch(`${API_BASE_URL}/auth/reset-password/`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) { showToast('Reset thành công.', 'success'); navigate('login'); }
        } catch (err) { showToast(err.message, 'error'); }
    });

    // Patients
    el('createPatientBtn')?.addEventListener('click', async () => {
        const payload = {
            full_name: el('patientFullName').value.trim(),
            date_of_birth: el('patientDob').value || null,
            gender: el('patientGender').value || null,
            notes: el('patientNotes').value.trim() || null
        };
        try {
            const url = state.editingPatientId
                ? `${API_BASE_URL}/patients/${state.editingPatientId}/`
                : `${API_BASE_URL}/patients/`;
            const res = await apiFetch(url, {
                method: state.editingPatientId ? 'PUT' : 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                showToast(state.editingPatientId ? 'Đã cập nhật bệnh nhân.' : 'Đã thêm bệnh nhân.', 'success');
                resetPatientForm();
                await loadPatients();
            }
        } catch (err) { showToast(err.message, 'error'); }
    });
    el('cancelPatientEditBtn')?.addEventListener('click', resetPatientForm);
    el('refreshHistoryBtn')?.addEventListener('click', loadPredictionHistory);
    el('patientSelect')?.addEventListener('change', () => {
        const patientId = el('patientSelect')?.value || '';
        if (el('predictionPatientSelect')) el('predictionPatientSelect').value = patientId;
        loadPredictionHistory();
    });
    el('historyPatientSelect')?.addEventListener('change', loadPredictionHistory);
    el('loadHistoryBtn')?.addEventListener('click', loadPredictionHistory);
    el('predictionPatientSelect')?.addEventListener('change', () => {
        const predictionId = el('predictionPatientSelect')?.value || '';
        if (el('patientSelect')) el('patientSelect').value = predictionId;
        renderPatients();
        loadPredictionHistory();
    });

    // Predictions
    el('sampleBenignBtn')?.addEventListener('click', () => loadSampleData('benign'));
    el('sampleMalignantBtn')?.addEventListener('click', () => loadSampleData('malignant'));
    el('predictMlBtn')?.addEventListener('click', predictMl);
    el('predictDlBtn')?.addEventListener('click', predictDl);
    el('predictFusionBtn')?.addEventListener('click', predictFusion);
    el('useFusionBenignDemoBtn')?.addEventListener('click', () => loadFusionDemo('benign'));
    el('useFusionMalignantDemoBtn')?.addEventListener('click', () => loadFusionDemo('malignant'));
    
    // File inputs
    el('imageInput')?.addEventListener('change', e => {
        const f = e.target.files?.[0]; if (!f) return;
        setSelectedDlImage(f, URL.createObjectURL(f), `Đã chọn: ${f.name}`);
    });
    el('useDemoBenignImageBtn')?.addEventListener('click', () => loadDemoDlImage('benign'));
    el('useDemoMalignantImageBtn')?.addEventListener('click', () => loadDemoDlImage('malignant'));
    el('importCsvBtn')?.addEventListener('click', () => el('csvInput').click());
    el('importReportImageBtn')?.addEventListener('click', () => el('reportImageInput').click());
    el('csvInput')?.addEventListener('change', e => {
        const f = e.target.files?.[0]; if (!f) return;
        const r = new FileReader();
        r.onload = () => {
            try {
                const payload = parseClinicalCsvText(r.result);
                fillClinicalValues(payload);
                showToast(`Đã nạp CSV: ${f.name}`, 'success');
            } catch (err) {
                showToast(err.message || 'CSV không hợp lệ.', 'error');
            }
        };
        r.readAsText(f);
    });
    el('reportImageInput')?.addEventListener('change', e => {
        const f = e.target.files?.[0]; if (!f) return;
        extractClinicalFromImage(f);
    });
    el('importFusionCsvBtn')?.addEventListener('click', () => el('fusionCsvInput')?.click());
    el('importFusionReportImageBtn')?.addEventListener('click', () => el('fusionReportImageInput')?.click());
    el('fusionCsvInput')?.addEventListener('change', e => {
        const f = e.target.files?.[0]; if (!f) return;
        const r = new FileReader();
        r.onload = () => {
            try {
                const payload = parseClinicalCsvText(r.result);
                const filled = setFusionClinicalValues(payload);
                showToast(`Đã nạp CSV kết hợp (${filled}/30): ${f.name}`, filled > 0 ? 'success' : 'error');
                switchPredictTab('fusion');
            } catch (err) {
                showToast(err.message || 'CSV kết hợp không hợp lệ.', 'error');
            }
        };
        r.readAsText(f);
    });
    el('fusionReportImageInput')?.addEventListener('change', e => {
        const f = e.target.files?.[0]; if (!f) return;
        extractClinicalFromImage(f, 'fusion');
    });
    el('fusionImageInput')?.addEventListener('change', e => {
        const f = e.target.files?.[0]; if (!f) return;
        setSelectedFusionImage(f, URL.createObjectURL(f), `Đã chọn ảnh kết hợp: ${f.name}`);
    });

    // Topbar UI
    el('avatarButton')?.addEventListener('click', ev => {
        ev.stopPropagation(); 
        el('avatarDropdown')?.classList.toggle('hidden');
    });
    document.addEventListener('click', () => el('avatarDropdown')?.classList.add('hidden'));

    // Mobile nav
    el('mobileNavToggle')?.addEventListener('click', openMobileNav);
    el('mobileNavDrawer')?.addEventListener('click', (ev) => { if (ev.target === el('mobileNavDrawer')) closeMobileNav(); });

    // Chatbot
    el('sendChatBtn')?.addEventListener('click', () => sendChatMessage());
    el('clearChatBtn')?.addEventListener('click', () => {
        state.chatTurns = [];
        localStorage.removeItem('bcai_guest_chat');
        setText('chatStatus', 'Đã xóa cuộc trò chuyện.');
        renderChat();
    });
    el('chatMessageInput')?.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter' && !ev.shiftKey) {
            ev.preventDefault();
            sendChatMessage();
        }
    });
    document.querySelectorAll('[data-chat-suggestion]').forEach((btn) => {
        btn.addEventListener('click', () => {
            navigate('assistant');
            sendChatMessage(btn.dataset.chatSuggestion || '');
        });
    });
    el('chatFab')?.addEventListener('click', () => navigate('assistant'));
}

function initialRoute() {
    const route = window.location.hash.replace('#', '').trim();
    navigate(VALID_PAGES.includes(route) ? route : 'home');
}

// ================================================================
// INIT
// ================================================================
document.addEventListener('DOMContentLoaded', async () => {
    renderStaticCollections();
    renderFeatureForm();
    bindFaqToggle();
    bindEvents();
    initialRoute();
    clearPredictionResult();
    updateMultimodalPanel();
    loadGuestChat();
    renderChat();
    await refreshAll();
});

window.addEventListener('hashchange', initialRoute);
