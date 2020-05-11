<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv65to66">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv65to66"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>6.5</literal> to <literal>6.6</literal>.
</para>
<xsl:template match="image" mode="conv65to66">
    <xsl:choose>
        <!-- nothing to do if already at 6.6 -->
        <xsl:when test="@schemaversion > 6.5">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="6.6">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv65to66"/>  
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<para xmlns="http://docbook.org/ns/docbook">
    Add xen_server attribute to type for dom0 configurations
</para>
<xsl:template match="type[machine[@domain='dom0']]" mode="conv65to66">
     <type>
         <xsl:copy-of select="@*"/>
         <xsl:attribute name="xen_server">
             <xsl:value-of select="'true'"/>
         </xsl:attribute>
         <xsl:apply-templates  mode="conv65to66"/>
     </type>
</xsl:template>

<para xmlns="http://docbook.org/ns/docbook">
    Delete domain attribute from machine sections
</para>
<xsl:template match="machine" mode="conv65to66">
    <machine>
        <xsl:copy-of select="@*[not(local-name(.) = 'domain')]"/>
        <xsl:variable name="domain_name" select="@domain"/>
        <xsl:apply-templates mode="conv65to66"/>
    </machine>
</xsl:template>

</xsl:stylesheet>
