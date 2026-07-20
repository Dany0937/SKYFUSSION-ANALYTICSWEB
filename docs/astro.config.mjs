// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	integrations: [
		starlight({
			title: 'Skyfussion Analytics',
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/withastro/starlight' }],
			sidebar: [
				{
					label: 'Arquitectura de Capas',
					items: [{ autogenerate: { directory: '00-architecture' } }],
				},
				{
					label: 'Manual de Agentes',
					items: [{ autogenerate: { directory: '01-agents' } }],
				},
				{
					label: 'Guía de Infraestructura',
					items: [{ autogenerate: { directory: '02-infrastructure' } }],
				},
				{
					label: 'API Reference',
					items: [{ autogenerate: { directory: '03-api-reference' } }],
				},
				{
					label: 'Engineering Standards',
					items: [{ autogenerate: { directory: '04-engineering-standards' } }],
				},
				{
					label: 'Guides',
					items: [{ autogenerate: { directory: 'guides' } }],
				},
				{
					label: 'Reference',
					items: [{ autogenerate: { directory: 'reference' } }],
				},
			],
		}),
	],
});
