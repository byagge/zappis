document.addEventListener('alpine:init', () => {
    Alpine.data('editorPage', () => ({
        selectedSection: 0,
        sections: [
            {
                id: 'header',
                name: 'Шапка',
                visible: true,
                content: {
                    title: 'Название сайта',
                    logo: null,
                    backgroundColor: '#ffffff',
                    textColor: '#1f2937'
                }
            },
            {
                id: 'main',
                name: 'Главный блок',
                visible: true,
                content: {
                    title: 'Заголовок главного блока',
                    description: 'Описание вашего бизнеса или услуги. Расскажите о своих преимуществах и уникальных предложениях.',
                    image: null,
                    backgroundColor: '#ffffff',
                    textColor: '#1f2937',
                    buttonBackgroundColor: '#2563eb',
                    buttonTextColor: '#ffffff'
                }
            },
            {
                id: 'services',
                name: 'Услуги',
                visible: true,
                content: {
                    title: 'Наши услуги',
                    description: 'Мы предлагаем широкий спектр услуг для вашего бизнеса',
                    services: [
                        {
                            title: 'Разработка сайтов',
                            description: 'Создание современных и функциональных веб-сайтов'
                        },
                        {
                            title: 'Дизайн',
                            description: 'Разработка уникального визуального стиля'
                        },
                        {
                            title: 'SEO-оптимизация',
                            description: 'Повышение видимости вашего сайта в поисковых системах'
                        }
                    ],
                    backgroundColor: '#f9fafb',
                    textColor: '#1f2937',
                    cardBackgroundColor: '#ffffff',
                    cardTextColor: '#4b5563',
                    buttonBackgroundColor: '#2563eb',
                    buttonTextColor: '#ffffff'
                }
            },
            {
                id: 'portfolio',
                name: 'Портфолио',
                visible: true,
                content: {
                    title: 'Наши работы',
                    works: [
                        { title: 'Работа 1', image: null },
                        { title: 'Работа 2', image: null },
                        { title: 'Работа 3', image: null }
                    ],
                    backgroundColor: '#f9fafb',
                    textColor: '#1f2937',
                    cardBackgroundColor: '#ffffff',
                    cardTextColor: '#1f2937'
                }
            },
            {
                id: 'contacts',
                name: 'Контакты',
                visible: true,
                content: {
                    title: 'Свяжитесь с нами',
                    description: 'Мы всегда на связи и готовы ответить на все ваши вопросы',
                    phone: '+7 (999) 123-45-67',
                    address: 'г. Москва, ул. Примерная, д. 1',
                    socials: [],
                    backgroundColor: '#ffffff',
                    textColor: '#1f2937'
                }
            }
        ],
        showDeleteModal: false,
        sectionToDelete: null,
        showSocialModal: false,
        showLinkModal: false,
        tempSocialLink: '',
        editingSocialIndex: null,
        socialNetworks: [
            { value: 'facebook', label: 'Facebook', si: 'facebook', color: '1877F2' },
            { value: 'instagram', label: 'Instagram', si: 'instagram', color: 'E4405F' },
            { value: 'twitter', label: 'X (twitter)', si: 'x', color: '000000' },
            { value: 'youtube', label: 'YouTube', si: 'youtube', color: 'FF0000' },
            { value: 'vk', label: 'VK', si: 'vk', color: '4A76A8' },
            { value: 'telegram', label: 'Telegram', si: 'telegram', color: '26A5E4' },
            { value: 'whatsapp', label: 'WhatsApp', si: 'whatsapp', color: '25D366' },
            { value: 'viber', label: 'Viber', si: 'viber', color: '7360F2' },
            { value: 'tiktok', label: 'TikTok', si: 'tiktok', color: '000000' },
            { value: 'pinterest', label: 'Pinterest', si: 'pinterest', color: 'E60023' },
            { value: 'tumblr', label: 'Tumblr', si: 'tumblr', color: '36465D' },
            { value: 'reddit', label: 'Reddit', si: 'reddit', color: 'FF4500' },
            { value: 'discord', label: 'Discord', si: 'discord', color: '5865F2' },
            { value: 'github', label: 'GitHub', si: 'github', color: '181717' },
            { value: 'behance', label: 'Behance', si: 'behance', color: '1769FF' },
            { value: 'dribbble', label: 'Dribbble', si: 'dribbble', color: 'EA4C89' },
            { value: 'medium', label: 'Medium', si: 'medium', color: '12100E' },
            { value: 'spotify', label: 'Spotify', si: 'spotify', color: '1ED760' },
            { value: 'soundcloud', label: 'SoundCloud', si: 'soundcloud', color: 'FF5500' },
            { value: 'twitch', label: 'Twitch', si: 'twitch', color: '9146FF' }
        ],
        lucideIcons: [
            'facebook', 'instagram', 'twitter', 'linkedin', 'youtube', 'vk', 'telegram', 'whatsapp', 'github', 'dribbble', 'behance', 'discord', 'skype', 'twitch'
        ],
        templates: [
            {
                name: 'Классический синий',
                colors: {
                    header: { backgroundColor: '#ffffff', textColor: '#1f2937' },
                    main: { backgroundColor: '#ffffff', textColor: '#1f2937', buttonBackgroundColor: '#2563eb', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#1f2937', cardBackgroundColor: '#ffffff', cardTextColor: '#4b5563', buttonBackgroundColor: '#2563eb', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#ffffff', textColor: '#1f2937', cardBackgroundColor: '#ffffff', cardTextColor: '#1f2937' },
                    contacts: { backgroundColor: '#1a365d', textColor: '#ffffff' },
                }
            },
            {
                name: 'Морская волна',
                colors: {
                    header: { backgroundColor: '#f0fdfa', textColor: '#0f766e' },
                    main: { backgroundColor: '#f0fdfa', textColor: '#0f766e', buttonBackgroundColor: '#14b8a6', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#0f766e', cardBackgroundColor: '#f0fdfa', cardTextColor: '#0d9488', buttonBackgroundColor: '#14b8a6', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#f0fdfa', textColor: '#0f766e', cardBackgroundColor: '#ffffff', cardTextColor: '#0d9488' },
                    contacts: { backgroundColor: '#0f766e', textColor: '#ffffff' },
                }
            },
            {
                name: 'Лавандовый закат',
                colors: {
                    header: { backgroundColor: '#faf5ff', textColor: '#6b21a8' },
                    main: { backgroundColor: '#faf5ff', textColor: '#6b21a8', buttonBackgroundColor: '#9333ea', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#6b21a8', cardBackgroundColor: '#faf5ff', cardTextColor: '#7e22ce', buttonBackgroundColor: '#9333ea', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#faf5ff', textColor: '#6b21a8', cardBackgroundColor: '#ffffff', cardTextColor: '#7e22ce' },
                    contacts: { backgroundColor: '#6b21a8', textColor: '#ffffff' },
                }
            },
            {
                name: 'Золотой песок',
                colors: {
                    header: { backgroundColor: '#fffbeb', textColor: '#92400e' },
                    main: { backgroundColor: '#fffbeb', textColor: '#92400e', buttonBackgroundColor: '#d97706', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#92400e', cardBackgroundColor: '#fffbeb', cardTextColor: '#b45309', buttonBackgroundColor: '#d97706', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#fffbeb', textColor: '#92400e', cardBackgroundColor: '#ffffff', cardTextColor: '#b45309' },
                    contacts: { backgroundColor: '#92400e', textColor: '#ffffff' },
                }
            },
            {
                name: 'Изумрудный сад',
                colors: {
                    header: { backgroundColor: '#ecfdf5', textColor: '#065f46' },
                    main: { backgroundColor: '#ecfdf5', textColor: '#065f46', buttonBackgroundColor: '#059669', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#065f46', cardBackgroundColor: '#ecfdf5', cardTextColor: '#047857', buttonBackgroundColor: '#059669', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#ecfdf5', textColor: '#065f46', cardBackgroundColor: '#ffffff', cardTextColor: '#047857' },
                    contacts: { backgroundColor: '#065f46', textColor: '#ffffff' },
                }
            },
            {
                name: 'Розовый рассвет',
                colors: {
                    header: { backgroundColor: '#fdf2f8', textColor: '#be185d' },
                    main: { backgroundColor: '#fdf2f8', textColor: '#be185d', buttonBackgroundColor: '#db2777', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#be185d', cardBackgroundColor: '#fdf2f8', cardTextColor: '#be185d', buttonBackgroundColor: '#db2777', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#fdf2f8', textColor: '#be185d', cardBackgroundColor: '#ffffff', cardTextColor: '#be185d' },
                    contacts: { backgroundColor: '#be185d', textColor: '#ffffff' },
                }
            },
            {
                name: 'Графитовый минимализм',
                colors: {
                    header: { backgroundColor: '#f9fafb', textColor: '#1f2937' },
                    main: { backgroundColor: '#f9fafb', textColor: '#1f2937', buttonBackgroundColor: '#374151', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#1f2937', cardBackgroundColor: '#f9fafb', cardTextColor: '#374151', buttonBackgroundColor: '#374151', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#f9fafb', textColor: '#1f2937', cardBackgroundColor: '#ffffff', cardTextColor: '#374151' },
                    contacts: { backgroundColor: '#1f2937', textColor: '#ffffff' },
                }
            },
            {
                name: 'Океанская глубина',
                colors: {
                    header: { backgroundColor: '#eff6ff', textColor: '#1e40af' },
                    main: { backgroundColor: '#eff6ff', textColor: '#1e40af', buttonBackgroundColor: '#2563eb', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#1e40af', cardBackgroundColor: '#eff6ff', cardTextColor: '#1d4ed8', buttonBackgroundColor: '#2563eb', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#eff6ff', textColor: '#1e40af', cardBackgroundColor: '#ffffff', cardTextColor: '#1d4ed8' },
                    contacts: { backgroundColor: '#1e40af', textColor: '#ffffff' },
                }
            },
            {
                name: 'Осенний листопад',
                colors: {
                    header: { backgroundColor: '#fff7ed', textColor: '#7c2d12' },
                    main: { backgroundColor: '#fff7ed', textColor: '#7c2d12', buttonBackgroundColor: '#c2410c', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#7c2d12', cardBackgroundColor: '#fff7ed', cardTextColor: '#9a3412', buttonBackgroundColor: '#c2410c', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#fff7ed', textColor: '#7c2d12', cardBackgroundColor: '#ffffff', cardTextColor: '#9a3412' },
                    contacts: { backgroundColor: '#7c2d12', textColor: '#ffffff' },
                }
            },
            {
                name: 'Лунная ночь',
                colors: {
                    header: { backgroundColor: '#f5f3ff', textColor: '#312e81' },
                    main: { backgroundColor: '#f5f3ff', textColor: '#312e81', buttonBackgroundColor: '#4f46e5', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#312e81', cardBackgroundColor: '#f5f3ff', cardTextColor: '#4338ca', buttonBackgroundColor: '#4f46e5', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#f5f3ff', textColor: '#312e81', cardBackgroundColor: '#ffffff', cardTextColor: '#4338ca' },
                    contacts: { backgroundColor: '#312e81', textColor: '#ffffff' },
                }
            },
            {
                name: 'Весенний сад',
                colors: {
                    header: { backgroundColor: '#f0fdf4', textColor: '#166534' },
                    main: { backgroundColor: '#f0fdf4', textColor: '#166534', buttonBackgroundColor: '#16a34a', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#166534', cardBackgroundColor: '#f0fdf4', cardTextColor: '#15803d', buttonBackgroundColor: '#16a34a', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#f0fdf4', textColor: '#166534', cardBackgroundColor: '#ffffff', cardTextColor: '#15803d' },
                    contacts: { backgroundColor: '#166534', textColor: '#ffffff' },
                }
            },
            {
                name: 'Коралловый риф',
                colors: {
                    header: { backgroundColor: '#fff1f2', textColor: '#be123c' },
                    main: { backgroundColor: '#fff1f2', textColor: '#be123c', buttonBackgroundColor: '#e11d48', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#be123c', cardBackgroundColor: '#fff1f2', cardTextColor: '#be123c', buttonBackgroundColor: '#e11d48', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#fff1f2', textColor: '#be123c', cardBackgroundColor: '#ffffff', cardTextColor: '#be123c' },
                    contacts: { backgroundColor: '#be123c', textColor: '#ffffff' },
                }
            },
            {
                name: 'Мятная свежесть',
                colors: {
                    header: { backgroundColor: '#f0fdf9', textColor: '#0d9488' },
                    main: { backgroundColor: '#f0fdf9', textColor: '#0d9488', buttonBackgroundColor: '#0d9488', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#0d9488', cardBackgroundColor: '#f0fdf9', cardTextColor: '#0d9488', buttonBackgroundColor: '#0d9488', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#f0fdf9', textColor: '#0d9488', cardBackgroundColor: '#ffffff', cardTextColor: '#0d9488' },
                    contacts: { backgroundColor: '#0d9488', textColor: '#ffffff' },
                }
            },
            {
                name: 'Сиреневая мечта',
                colors: {
                    header: { backgroundColor: '#faf5ff', textColor: '#7e22ce' },
                    main: { backgroundColor: '#faf5ff', textColor: '#7e22ce', buttonBackgroundColor: '#7e22ce', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#7e22ce', cardBackgroundColor: '#faf5ff', cardTextColor: '#7e22ce', buttonBackgroundColor: '#7e22ce', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#faf5ff', textColor: '#7e22ce', cardBackgroundColor: '#ffffff', cardTextColor: '#7e22ce' },
                    contacts: { backgroundColor: '#7e22ce', textColor: '#ffffff' },
                }
            },
            {
                name: 'Небесная лазурь',
                colors: {
                    header: { backgroundColor: '#f0f9ff', textColor: '#0369a1' },
                    main: { backgroundColor: '#f0f9ff', textColor: '#0369a1', buttonBackgroundColor: '#0369a1', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#0369a1', cardBackgroundColor: '#f0f9ff', cardTextColor: '#0369a1', buttonBackgroundColor: '#0369a1', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#f0f9ff', textColor: '#0369a1', cardBackgroundColor: '#ffffff', cardTextColor: '#0369a1' },
                    contacts: { backgroundColor: '#0369a1', textColor: '#ffffff' },
                }
            },
            {
                name: 'Шоколадная элегантность',
                colors: {
                    header: { backgroundColor: '#fef3c7', textColor: '#92400e' },
                    main: { backgroundColor: '#fef3c7', textColor: '#92400e', buttonBackgroundColor: '#92400e', buttonTextColor: '#ffffff' },
                    services: { backgroundColor: '#ffffff', textColor: '#92400e', cardBackgroundColor: '#fef3c7', cardTextColor: '#92400e', buttonBackgroundColor: '#92400e', buttonTextColor: '#ffffff' },
                    portfolio: { backgroundColor: '#fef3c7', textColor: '#92400e', cardBackgroundColor: '#ffffff', cardTextColor: '#92400e' },
                    contacts: { backgroundColor: '#92400e', textColor: '#ffffff' },
                }
            }
        ],
        socialSearch: '',
        filteredSocialNetworks: [],
        currentPage: 1,
        itemsPerPage: 12,
        init() {
            localStorage.clear();
            
            const savedData = localStorage.getItem('siteData');
            if (savedData) {
                this.sections = JSON.parse(savedData);
            } else {
                this.applyTemplate(this.templates[0]);
            }

            this.filteredSocialNetworks = [...this.socialNetworks];
            this.$watch('socialSearch', () => this.currentPage = 1);
        },
        get totalPages() {
            return Math.ceil(this.filteredSocialNetworks.length / this.itemsPerPage);
        },
        get paginatedSocialNetworks() {
            const start = (this.currentPage - 1) * this.itemsPerPage;
            const end = start + this.itemsPerPage;
            return this.filteredSocialNetworks.slice(start, end);
        },
        editSection(index) {
            this.selectedSection = index;
        },
        toggleSection(index) {
            const section = this.sections[index];
            if (section.id !== 'header' && section.id !== 'main') {
                section.visible = !section.visible;
            }
        },
        deleteSection(index) {
            const section = this.sections[index];
            if (section.id !== 'header' && section.id !== 'main') {
                this.sectionToDelete = section.id;
                this.showDeleteModal = true;
            }
        },
        confirmDelete() {
            if (this.sectionToDelete !== null) {
                this.sections = this.sections.filter(section => section.id !== this.sectionToDelete);
                this.selectedSection = null;
                this.sectionToDelete = null;
                this.showDeleteModal = false;
            }
        },
        addWork() {
            const portfolioSection = this.sections.find(s => s.id === 'portfolio');
            if (portfolioSection) {
                portfolioSection.content.works.push({
                title: 'Новая работа',
                image: null
            });
            }
        },
        removeWork(index) {
            const portfolioSection = this.sections.find(s => s.id === 'portfolio');
            if (portfolioSection) {
                portfolioSection.content.works.splice(index, 1);
            }
        },
        uploadLogo(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const headerSection = this.sections.find(s => s.id === 'header');
                    if (headerSection) {
                        headerSection.content.logo = e.target.result;
                    }
                };
                reader.readAsDataURL(file);
            }
        },
        uploadMainImage(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const mainSection = this.sections.find(s => s.id === 'main');
                    if (mainSection) {
                        mainSection.content.image = e.target.result;
                    }
                };
                reader.readAsDataURL(file);
            }
        },
        uploadWorkImage(index, event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const portfolioSection = this.sections.find(s => s.id === 'portfolio');
                    if (portfolioSection) {
                        portfolioSection.content.works[index].image = e.target.result;
                    }
                };
                reader.readAsDataURL(file);
            }
        },
        saveChanges() {
            localStorage.setItem('siteData', JSON.stringify(this.sections));
            console.log('Изменения сохранены');
        },
        previewSite() {
            console.log('Предпросмотр сайта...');
        },
        selectSocialNetwork(network) {
            this.showSocialModal = false;
            this.tempSocialLink = '';
            this.editingSocialIndex = null;
            const contactsSection = this.sections.find(s => s.id === 'contacts');
            if (contactsSection) {
                contactsSection.content.socials.push({
                    icon: network,
                    link: ''
                });
                setTimeout(() => {
                    this.showLinkModal = true;
                    lucide.createIcons();
                }, 100);
            }
        },
        editSocialLink(index) {
            const contactsSection = this.sections.find(s => s.id === 'contacts');
            if (contactsSection) {
                this.tempSocialLink = contactsSection.content.socials[index].link;
                this.editingSocialIndex = index;
                this.showLinkModal = true;
            }
        },
        saveSocialLink() {
            const contactsSection = this.sections.find(s => s.id === 'contacts');
            if (contactsSection) {
                if (this.editingSocialIndex !== null) {
                    contactsSection.content.socials[this.editingSocialIndex].link = this.tempSocialLink;
                } else {
                    const lastIndex = contactsSection.content.socials.length - 1;
                    contactsSection.content.socials[lastIndex].link = this.tempSocialLink;
                }
            }
            this.showLinkModal = false;
            this.tempSocialLink = '';
            this.editingSocialIndex = null;
        },
        getSocialNetworkName(icon) {
            const network = this.socialNetworks.find(n => n.value === icon);
            return network ? network.label : icon;
        },
        removeSocial(index) {
            const contactsSection = this.sections.find(s => s.id === 'contacts');
            if (contactsSection) {
                contactsSection.content.socials.splice(index, 1);
                setTimeout(() => {
                    lucide.createIcons();
                }, 0);
            }
        },
        filterSocialNetworks() {
            if (!this.socialSearch) {
                this.filteredSocialNetworks = [...this.socialNetworks];
            } else {
                const search = this.socialSearch.toLowerCase();
                this.filteredSocialNetworks = this.socialNetworks.filter(network => 
                    network.label.toLowerCase().includes(search)
                );
            }
            this.currentPage = 1;
        },
        nextPage() {
            if (this.currentPage < this.totalPages) {
                this.currentPage++;
            }
        },
        prevPage() {
            if (this.currentPage > 1) {
                this.currentPage--;
            }
        },
        applyTemplate(template) {
            // Применяем цвета темы к секциям
            Object.keys(template.colors).forEach(sectionId => {
                const section = this.sections.find(s => s.id === sectionId);
                if (section) {
                    Object.assign(section.content, template.colors[sectionId]);
                }
            });
        },
        // Функция для обновления предварительного просмотра
        updatePreview() {
            const iframe = document.querySelector('.preview-iframe');
            if (iframe) {
                // Перезагружаем iframe для обновления предварительного просмотра
                iframe.src = iframe.src;
            }
        },
        // Функция для сохранения изменений в user.html
        saveToUserHtml() {
            // Здесь можно добавить логику для сохранения изменений в user.html
            console.log('Сохранение изменений в user.html...');
            this.updatePreview();
        }
    }));
});

document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
});