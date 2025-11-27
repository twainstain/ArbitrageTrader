import { Box, Container, Typography, Grid, Card, CardContent } from '@mui/material';
import CodeIcon from '@mui/icons-material/Code';
import StorageIcon from '@mui/icons-material/Storage';
import PsychologyIcon from '@mui/icons-material/Psychology';
import { keyframes } from '@mui/system';

// Removed distracting float animation for professional look

const services = [
  {
    icon: <CodeIcon sx={{ fontSize: 50 }} />,
    title: 'Software Development',
    description: 'Custom software solutions tailored to your business needs. From web applications to enterprise systems, we build scalable and robust software.',
    color: '#3B82F6',  // Blue for Software
  },
  {
    icon: <StorageIcon sx={{ fontSize: 50 }} />,
    title: 'Data Engineering',
    description: 'Transform raw data into actionable insights. We design data pipelines, warehouses, and analytics platforms that power informed decisions.',
    color: '#22C55E',  // Green for Data
  },
  {
    icon: <PsychologyIcon sx={{ fontSize: 50 }} />,
    title: 'AI & Machine Learning',
    description: 'Leverage the power of artificial intelligence. We develop intelligent systems, predictive models, and automation solutions.',
    color: '#A855F7',  // Purple for AI/ML
  },
];

const Services = () => {
  return (
    <Box id="services" sx={{
      py: 12,
      background: 'linear-gradient(180deg, #0B1426 0%, #132238 100%)',
      position: 'relative',
    }}>
      <Container maxWidth="lg">
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Typography variant="overline" sx={{ color: '#64B4FF', letterSpacing: 3, fontWeight: 500 }}>
            What We Offer
          </Typography>
          <Typography variant="h2" sx={{
            fontSize: { xs: '2rem', md: '2.75rem' },
            fontWeight: 600,
            color: '#E2E8F0',
            mt: 1,
            letterSpacing: '-0.5px',
          }}>
            Our Services
          </Typography>
        </Box>
        <Grid container spacing={4}>
          {services.map((service, index) => (
            <Grid key={service.title} size={{ xs: 12, md: 4 }}>
              <Card sx={{
                height: '100%',
                background: 'rgba(20, 25, 45, 0.8)',
                backdropFilter: 'blur(10px)',
                border: `1px solid ${service.color}30`,
                borderRadius: 3,
                transition: 'all 0.3s ease',
                '&:hover': {
                  borderColor: service.color,
                  transform: 'translateY(-5px)',
                  boxShadow: `0 10px 30px ${service.color}20`,
                },
              }}>
                <CardContent sx={{ p: 4, textAlign: 'center' }}>
                  <Box sx={{
                    width: 100, height: 100, mx: 'auto', mb: 3,
                    borderRadius: '50%',
                    background: `linear-gradient(135deg, ${service.color}20, ${service.color}10)`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    border: `2px solid ${service.color}40`,
                    color: service.color,
                  }}>
                    {service.icon}
                  </Box>
                  <Typography variant="h5" sx={{ color: 'white', fontWeight: 600, mb: 2 }}>
                    {service.title}
                  </Typography>
                  <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.7)', lineHeight: 1.8 }}>
                    {service.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
};

export default Services;

