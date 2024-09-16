<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv62to63">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv62to63"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>6.2</literal> to <literal>6.3</literal>.
</para>
<xsl:template match="image" mode="conv62to63">
    <xsl:choose>
        <!-- nothing to do if already at 6.3 -->
        <xsl:when test="@schemaversion > 6.2">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="6.3">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv62to63"/>  
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv62to63">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv62to63"/>
    </xsl:copy>
</xsl:template>

<para xmlns="http://docbook.org/ns/docbook">
    Remove obsolete fsreadonly, fsreadwrite and zfsoptions attributes from types
</para>
<xsl:template match="type" mode="conv62to63">
    <type>
        <xsl:copy-of select="@*[not(local-name(.) = 'fsreadonly') and not(local-name(.) = 'fsreadwrite') and not(local-name(.) = 'zfsoptions')]"/>
        <xsl:apply-templates mode="conv62to63"/>
    </type>
</xsl:template>

<para xmlns="http://docbook.org/ns/docbook">
    Remove obsolete split section
</para>
<xsl:template match="split" mode="conv62to63">
    <xsl:apply-templates mode="conv62to63"/>
</xsl:template>

</xsl:stylesheet>
